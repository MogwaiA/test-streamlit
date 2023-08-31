import streamlit as st
from useful_functions import *

def rapports_seismes():
    # Personnalisation de la mise en page avec du code HTML
    st.markdown("<h1 style='text-align: left;'>Rapports en temps réel</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: left;'>Visualisation des sites impactés</h2>", unsafe_allow_html=True)

    # Ajouter un widget de chargement de fichier
    uploaded_file = st.file_uploader("Charger une liste de coordonnées géographiques", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Charger les données à partir du fichier
        df = load_data(uploaded_file)

           # Widget pour choisir la période
    st.markdown("<h3>Choisir une période :</h3>", unsafe_allow_html=True)
    period = st.selectbox(
        "Sélectionnez la période",
        ["Un jour", "Trois jours", "Une semaine", "Un mois", "6 mois", "Un an"]
    )

    # Afficher le message d'avertissement
    if period in ["Un mois", "6 mois", "Un an"]:
        st.warning("Attention : plus la période choisie est longue, plus le temps d'exécution sera élevé.")

    # Convertir la période en nombre de jours
    period_days = {
        "Un jour": 1,
        "Trois jours": 3,
        "Une semaine": 7,
        "Un mois": 30,
        "6 mois": 180,
        "Un an": 365
    }
    selected_days = period_days[period]

    st.write(f"Période sélectionnée : {period} ({selected_days} jours)")

  






