from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd

app = FastAPI(
    title="API Indicateurs Galeon",
    description="API calculant dynamiquement les indicateurs hospitaliers à partir des données nettoyées.",
    version="1.0.0"
)

def load_clean_data():
    df = pd.read_csv('sejours_clean.csv')
    df['date_entree'] = pd.to_datetime(df['date_entree'])
    df['date_sortie'] = pd.to_datetime(df['date_sortie'])
    return df

@app.get("/")
def read_root():
    return {"statut": "API en ligne", "message": "Bienvenue sur l'API Galeon"}

@app.get("/api/indicateurs/dms")
def get_dms():
    """Calcule et retourne la Durée Moyenne de Séjour (DMS) par service."""
    df = load_clean_data()
    df_term = df.dropna(subset=['date_sortie']).copy()
    df_term['DMS'] = (df_term['date_sortie'] - df_term['date_entree']).dt.days
    stats = df_term.groupby('service')['DMS'].agg(['mean', 'median']).round(1)
    resultat = stats.to_dict(orient='index')
    
    return JSONResponse(content={
        "indicateur": "Durée Moyenne de Séjour (DMS) par service",
        "unite": "jours",
        "valeurs": resultat
    })

@app.get("/api/indicateurs/rehospitalisation")
def get_rehospitalisation():
    """Calcule et retourne le taux de réhospitalisation global à 30 jours."""
    df = load_clean_data()
    df_term = df.dropna(subset=['date_sortie'])
    df_tri = df.sort_values(['id_patient', 'date_entree'])
    delai = (df_tri['date_entree'] - df_tri.groupby('id_patient')['date_sortie'].shift()).dt.days
    taux = (delai.between(0, 30).sum() / len(df_term)) * 100
    
    return JSONResponse(content={
        "indicateur": "Taux de réhospitalisation à 30 jours", 
        "valeur": round(taux, 2), 
        "unite": "%"
    })

@app.get("/api/indicateurs/flux")
def get_flux():
    """Calcule le flux d'entrées mensuel par service."""
    df = load_clean_data()
    df['mois'] = df['date_entree'].dt.strftime('%Y-%m')
    flux_mensuel = pd.crosstab(df['mois'], df['service'])
    resultat = flux_mensuel.to_dict(orient='index')
    
    return JSONResponse(content={
        "indicateur": "Flux d'entrées mensuel par service",
        "valeurs": resultat
    })