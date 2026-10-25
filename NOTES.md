## Partie 2 — Question de conception : API en production

Avant d'exposer des données patients en production, j'implémenterais 3 sécurités obligatoires :
1. **Authentification (JWT / OAuth2) :** Bloquer les routes pour s'assurer que seul le personnel autorisé (ex: médecins, DIM) y accède.
2. **Chiffrement (HTTPS/TLS) :** Forcer un canal sécurisé pour que les données de santé ne transitent jamais en clair sur le réseau.
3. **Traçabilité (Logs d'audit) :** Enregistrer chaque appel API (qui a consulté quoi, quand) pour être conforme aux exigences du RGPD et de l'hébergement HDS.

## Partie 4 — Audit de la collection constantes et choix de nettoyage

En explorant le dump MongoDB des constantes, j'ai repéré plusieurs anomalies métiers. Voici le tableau récapitulatif des problèmes trouvés et comment je les ai traités explicitement dans mon script pour les exports 4.1 à 4.3 :

| Type d'anomalie | Exemple trouvé dans la base | Traitement appliqué dans le script Python |
| :--- | :--- | :--- |
| **Unités incohérentes** | Les glycémies sont saisies soit en `mmol/L`, soit en `mg/dL` (ex: 252 mg/dL pour le patient `eda7...`). | **Filtre (4.1) :** Harmonisation conditionnelle. Les valeurs en `mg/dL` sont divisées par 18.0, et la colonne unité est forcée à `mmol/L`. |
| **Valeurs aberrantes (Outliers)** | Une température est saisie à `372.0` °C (patient `9ef2...`). C'est un oubli de virgule classique lors de la frappe. | **Filtre (4.3) :** Redressement des erreurs de frappe. Les températures `> 100` sont divisées par 10 pour récupérer la valeur physiologique (ex: 37.2°C). |
| **Appariement Sys/Dia** | Les tensions systoliques et diastoliques sont des lignes distinctes (code `ta_sys` et `ta_dia`). | **Filtre (4.2) :** Utilisation d'un `pivot_table` sur la date exacte (`date_mesure`) suivi d'un `.dropna()` pour s'assurer qu'elles ont été mesurées au même instant précis. |
| **Doublons stricts** | Des constantes identiques (patient, date, valeur) liées à des doubles-clics logiciels. | **Doublons :** Utilisation de `drop_duplicates()` après le nettoyage pour ne garder qu'une ligne unique par mesure. |
| **Format des dates** | L'export natif imbrique les dates dans un dictionnaire de type `{"$date": "..."}`. | **Parsing :** Boucle dans la fonction de chargement Python pour extraire la date proprement avant la conversion par Pandas. |

---

## Question de conception : Passage à l'échelle (Base de 40 millions de constantes)

Actuellement, mon script charge les données brutes en mémoire pour les traiter avec Pandas. Si on lance ça tel quel sur une base de production de 40 millions de lignes, le serveur va inévitablement crasher. 

Pour industrialiser ces exports mensuels, voici les 3 choses que je changerais dans mon approche :

**1. Faire le gros du calcul directement côté base de données (MongoDB Aggregation Pipelines)**
Au lieu d'importer toutes les données en Python pour les filtrer, j'écrirais des pipelines d'agrégation natifs dans MongoDB. Par exemple, on ferait le `$match` (pour filtrer les glycémies) et le `$lookup` (pour faire la jointure avec les patients diabétiques) directement sur le serveur de la base de données. Python ne servirait plus qu'à récupérer le tableau final (qui fera quelques milliers de lignes tout au plus) et à l'écrire en CSV.

**2. Ajouter des index composés**
Pour éviter que MongoDB ne lise les 40 millions de lignes à chaque fois qu'on lance l'export (*Full Collection Scan*), je demanderais à ce qu'on pose des index ciblés sur les champs utilisés dans nos filtres. 
*Exemple d'index vital pour l'export 4.2 :* `{ "code": 1, "contexte.ref_id": 1, "date_mesure": 1 }`.

**3. Traitement incrémental (Delta)**
Comme c'est un export qui tourne tous les mois, il est inutile de recalculer tout l'historique depuis la création de l'hôpital. J'ajouterais un filtre sur la date d'insertion pour ne requêter que les données du mois précédent.