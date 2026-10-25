# Test Technique Galeon - Analyse de Données & API

Ce dépôt contient la solution complète du test technique pour Galeon. Le projet couvre le nettoyage de données hospitalières (DPI), le calcul d'indicateurs de performance, leur exposition via une API REST, ainsi que des réflexions d'architecture et de normes de santé.

## Structure du projet

- **`Partie1.ipynb` (Partie 1)** : Notebook d'audit, de nettoyage (génération de `sejours_clean.csv`) et d'analyse exploratoire (DMS, flux, réhospitalisation).
- **`main.py` (Partie 2)** : Backend HTTP développé avec FastAPI exposant les indicateurs métiers.
- **`export_galeon.py` (Partie 4)** : Script d'ingénierie de données traitant les exports MongoDB (gestion des anomalies, conversion d'unités, agrégations) pour générer les exports finaux au format CSV.
- **`NOTES.md` et `REPONSES.md` (Partie 3 & Conception)** : Livrables théoriques sur l'architecture (scalabilité MongoDB), la sécurité (RGPD/HDS) et l'interopérabilité (HL7 FHIR).
- **`requirements.txt`** : Liste des dépendances Python du projet.

---

## Installation & Prérequis

Il est recommandé d'utiliser un environnement virtuel. À la racine du projet, exécutez les commandes suivantes.

### 1. Créer l'environnement virtuel

```bash
python -m venv venv
```

### 2. Activer l'environnement virtuel

**Sur macOS/Linux :**

```bash
source venv/bin/activate
```

**Sur Windows :**

```bash
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Exécution de l'analyse et du nettoyage (Partie 1)
Pour exécuter le notebook `Partie1.ipynb`, placez le fichier brut sejours.csv à la racine du projet.
L'exécution de ce notebook générera le fichier fiabilisé `sejours_clean.csv`, qui est indispensable pour le fonctionnement de l'API.

---

## Lancement de l'API (Partie 2)

L'API calcule dynamiquement les indicateurs à partir du fichier `sejours_clean.csv`.

Pour démarrer le serveur local de développement, exécutez :

```bash
uvicorn main:app --reload
```

Le serveur sera accessible à l'adresse suivante :

[http://127.0.0.1:8000](http://127.0.0.1:8000)

### Documentation interactive (Swagger UI)

La documentation générée automatiquement est disponible à l'adresse suivante. Elle permet de tester directement les routes depuis le navigateur :

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Exemples d'appels cURL

#### 1. Vérifier le statut de l'API

```bash
curl -X GET "http://127.0.0.1:8000/" \
  -H "accept: application/json"
```

#### 2. Récupérer la durée moyenne de séjour (DMS) par service

```bash
curl -X GET "http://127.0.0.1:8000/api/indicateurs/dms" \
  -H "accept: application/json"
```

#### 3. Récupérer le taux de réhospitalisation global à 30 jours

```bash
curl -X GET "http://127.0.0.1:8000/api/indicateurs/rehospitalisation" \
  -H "accept: application/json"
```

#### 4. Récupérer le flux mensuel d'entrées

```bash
curl -X GET "http://127.0.0.1:8000/api/indicateurs/flux" \
  -H "accept: application/json"
```

---

## Exécution des scripts de données (Partie 4)

Pour générer les fichiers CSV d'exports métiers (glycémies, tension, fièvres), placez les fichiers bruts suivants dans un dossier `mongo_test/` à la racine du projet :

- `patients.json`
- `sejours.json`
- `constantes.json`
- `praticiens.json`
- `consultations.json`

Lancez ensuite le script :

```bash
python export_galeon.py
```
