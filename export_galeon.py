import pandas as pd
import json

# --- 1. FONCTIONS DE CHARGEMENT ---
def charger_mongo(chemin):
    """Lit le JSON ligne par ligne et nettoie les formats spécifiques à MongoDB."""
    donnees = []
    with open(chemin, 'r', encoding='utf-8') as f:
        for ligne in f:
            doc = json.loads(ligne)
            
            # On sort les infos du contexte pour créer des colonnes simples
            if 'contexte' in doc:
                doc['contexte_type'] = doc['contexte'].get('type')
                doc['contexte_ref_id'] = doc['contexte'].get('ref_id')
            
            # On extrait la date propre du dictionnaire {"$date": "..."}
            champs_dates = ['date_mesure', 'date_naissance', 'date_entree', 'date_sortie', 'date']
            for champ in champs_dates:
                if champ in doc and type(doc[champ]) == dict:
                    doc[champ] = doc[champ].get('$date')
                
            donnees.append(doc)
    return pd.DataFrame(donnees)

print("Chargement des données...")
df_patients = charger_mongo('mongo_test/patients.json')
df_sejours = charger_mongo('mongo_test/sejours.json')
df_constantes = charger_mongo('mongo_test/constantes.json')

df_constantes['date_mesure'] = pd.to_datetime(df_constantes['date_mesure'])
df_sejours['date_entree'] = pd.to_datetime(df_sejours['date_entree'])
df_sejours['date_sortie'] = pd.to_datetime(df_sejours['date_sortie'])


# --- 4.1 Glycémies des patients diabétiques (2025) ---
print("Export 4.1...")

def a_le_diabete(liste_codes):
    if type(liste_codes) != list:
        return False
    for code in liste_codes:
        if str(code).startswith('E1'):
            return True
    return False

# On cherche les diabétiques dans les antécédents ET dans les diagnostics de séjour
diab_ant = df_patients[df_patients['antecedents'].apply(a_le_diabete)]['_id']
diab_sej = df_sejours[df_sejours['diagnostics'].apply(a_le_diabete)]['patient_id']
tous_diabetiques = set(diab_ant).union(set(diab_sej))

# On filtre les constantes selon les critères demandés
df_glyc = df_constantes[
    (df_constantes['code'] == 'glycemie') & 
    (df_constantes['date_mesure'].dt.year == 2025) &
    (df_constantes['patient_id'].isin(tous_diabetiques))
].copy()

# Nettoyage métier : conversion des mg/dL en mmol/L (division par 18)
df_glyc.loc[df_glyc['unite'] == 'mg/dL', 'valeur'] = df_glyc['valeur'] / 18.0
df_glyc['unite'] = 'mmol/L'
df_glyc['valeur'] = df_glyc['valeur'].round(1)

# On enlève les valeurs absurdes et les doublons de clics
df_glyc = df_glyc[(df_glyc['valeur'] > 0) & (df_glyc['valeur'] < 50)]
df_glyc = df_glyc.drop_duplicates(subset=['patient_id', 'date_mesure', 'code'])

colonnes_finales = ['_id', 'patient_id', 'contexte_type', 'contexte_ref_id', 'valeur', 'unite', 'date_mesure']
df_glyc[colonnes_finales].to_csv('export_4_1_glycemies.csv', index=False)


# --- 4.2 Évolution tensionnelle par séjour ---
print("Export 4.2...")

# On ne garde que les séjours terminés
df_sej_clos = df_sejours[df_sejours['statut'] == 'clos'].dropna(subset=['date_sortie']).copy()

# Calcul de la durée exacte en heures
df_sej_clos['duree_h'] = (df_sej_clos['date_sortie'] - df_sej_clos['date_entree']) / pd.Timedelta(hours=1)

sejours_cibles = df_sej_clos[
    (df_sej_clos['duree_h'] >= 48) & 
    (df_sej_clos['service'].isin(['MED', 'CARDIO', 'GER']))
]['_id']

# On isole les tensions de ces séjours précis
df_ta = df_constantes[
    (df_constantes['code'].isin(['ta_sys', 'ta_dia'])) & 
    (df_constantes['contexte_type'] == 'sejour') & 
    (df_constantes['contexte_ref_id'].isin(sejours_cibles))
].copy()

# Pivot : permet de mettre la Systolique et la Diastolique sur la même ligne (garantit qu'elles sont prises au même instant)
df_ta_pivot = df_ta.pivot_table(index=['contexte_ref_id', 'date_mesure'], columns='code', values='valeur').dropna().reset_index()
df_ta_pivot = df_ta_pivot.sort_values(['contexte_ref_id', 'date_mesure'])

# On isole la première et la dernière mesure du séjour
ta_first = df_ta_pivot.groupby('contexte_ref_id').first().reset_index()
ta_last = df_ta_pivot.groupby('contexte_ref_id').last().reset_index()

# On fusionne pour faire la soustraction finale
df_evo = pd.merge(ta_first, ta_last, on='contexte_ref_id', suffixes=('_debut', '_fin'))
df_evo['variation_systolique'] = df_evo['ta_sys_fin'] - df_evo['ta_sys_debut']

df_evo.to_csv('export_4_2_evolution_ta.csv', index=False)


# --- 4.3 Fièvre en consultation puis hospitalisation ---
print("Export 4.3...")

df_temp = df_constantes[df_constantes['code'] == 'temp'].copy()

# Traitement anomalie : correction de la virgule oubliée (ex: 372.0 devient 37.2)
df_temp.loc[df_temp['valeur'] > 100, 'valeur'] = df_temp['valeur'] / 10.0

# On isole les fièvres identifiées en consultation
mask_fievre = (df_temp['valeur'] >= 38.5) & (df_temp['contexte_type'] == 'consultation')
df_fievre = df_temp[mask_fievre][['patient_id', 'date_mesure']].rename(columns={'date_mesure': 'date_fievre'})

# On croise avec les dates d'entrée à l'hôpital
df_croise = pd.merge(df_fievre, df_sejours[['patient_id', 'date_entree', '_id']], on='patient_id')

# Calcul en secondes pour avoir le délai mathématique exact (évite les arrondis de jours de Pandas)
df_croise['delai_jours'] = (df_croise['date_entree'] - df_croise['date_fievre']).dt.total_seconds() / (24*3600)

# On garde les hospitalisations ayant eu lieu dans les 7 jours (168h) suivant la fièvre
res_43 = df_croise[(df_croise['delai_jours'] >= 0) & (df_croise['delai_jours'] <= 7)]
res_43.to_csv('export_4_3_fievre_hospit.csv', index=False)

print("Tous les exports sont générés !")