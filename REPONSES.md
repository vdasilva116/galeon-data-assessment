## Partie 3 — IA en santé : réflexion

### 3.1 — Modèle prédictif (Score de risque)
Pour enrichir le dataset, j'irais d'abord chercher des données cliniques (constantes vitales, résultats labo avant la sortie), l'historique médicamenteux et quelques variables socio-démographiques (distance au domicile, isolement). Côté modèle, je commencerais simple avec une **Régression Logistique pénalisée** ou un Random Forest. C'est robuste, et surtout l'explicabilité est top (on peut facilement voir le poids de chaque *feature*), ce qui est indispensable pour que les médecins fassent confiance à l'outil. 

Pour l'évaluation, vu qu'on a un fort déséquilibre de classes (autour de 5% de réhospitalisations), l'*Accuracy* ne sert à rien. Je ciblerais plutôt le **Recall** et l'**AUC-PR** : dans ce contexte, il vaut mieux avoir des faux positifs (déclencher une alerte préventive pour rien) que des faux négatifs (laisser sortir un patient à risque). Le plus gros danger pour moi serait un **biais socio-économique** : le modèle pourrait apprendre que la précarité entraîne plus de retours (faute de suivi en ville) et l'hôpital pourrait être tenté de garder ces patients plus longtemps artificiellement.

### 3.2 — Mise en situation (ChatGPT aux urgences)
Je lui dis de ne pas le faire ! L'idée d'automatiser pour gagner du temps est super, mais brancher ChatGPT directement pose d'énormes problèmes :
1. **RGPD & Secret médical :** Envoyer des données de santé personnelles sur les serveurs d'OpenAI est illégal en l'état. Leurs serveurs grand public ne sont pas certifiés HDS (Hébergeur de Données de Santé).
2. **Fuite de données :** Les prompts tapés dans les versions gratuites peuvent servir à entraîner le modèle. On ne peut pas risquer qu'une info patient ressorte chez un autre utilisateur.
3. **Hallucinations :** Un LLM peut très bien inventer un traitement ou un dosage qui a l'air crédible. Sur une lettre de sortie, le risque médico-légal est trop grand.

**Mon plan d'action :** On oublie son compte perso, mais je lui propose de monter un petit PoC en interne avec un modèle Open Source (comme un Mistral ou un Llama 3) hébergé sur nos propres serveurs sécurisés, ou alors on passe par une API d'entreprise certifiée HDS (comme Azure OpenAI) sans réutilisation des données.

### 3.3 — Interopérabilité
On croise souvent plusieurs standards en santé : HL7 v2 (c'est ancien et lourd), OMOP CDM (top pour la recherche et les bases de données), ou CDA (pour les documents). 

**Mon choix : HL7 FHIR sans hésiter.** 
C'est le standard actuel. Techniquement, c'est beaucoup plus sympa et naturel à manipuler pour un développeur parce que ça repose sur des API REST et du JSON. Envoyer notre score en format FHIR garantit qu'il sera lisible facilement par n'importe quel entrepôt régional ou le Health Data Hub.

### 3.4 — Veille (Article ou outil marquant et ses limites)

**Ce qui m'a marqué :** L'arrivée des petits LLMs multimodaux Open Source appliqués à la santé. Récemment, j'ai lu un papier de début 2026 (*LLaMA32-Med*) qui montre comment adapter le modèle Llama 3.2 Vision (de Meta) à l'imagerie et aux textes médicaux avec une méthode ultra-légère. Ce qui est fou, c'est qu'on a enfin des modèles capables de regarder une radio tout en lisant le dossier du patient, et surtout, ils sont assez légers pour tourner **en local sur les serveurs d'un hôpital**. Ça règle d'un coup l'énorme frein du RGPD et du secret médical lié au cloud. 

**Ce qui me semble surestimé :** Le discours médiatique qui conclut direct que "l'IA multimodale va remplacer le radiologue". Réussir un test de diagnostic sur un jeu de données parfait et bien nettoyé en laboratoire, c'est une chose. Mais dans la vraie vie (aux urgences par exemple), la donnée est hyper bruitée : la radio est floue ou mal centrée, le patient explique mal ses symptômes, l'historique est incomplet. Je trouve qu'on surestime largement la capacité actuelle de ces modèles à gérer le côté "chaotique" et l'incertitude du terrain. L'IA reste aujourd'hui un excellent "copilote" pour trier ou prérédiger.

*(Source : "LLaMA32-Med: Parameter-Efficient Adaptation of Multimodal LLMs for Medical Visual Question Answering", MIDL 2026 - https://openreview.net/forum?id=qGgZZwEeef)*