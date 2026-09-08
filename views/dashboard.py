import pandas as pd
import streamlit as st
from config import DOMAINES_SURETE, STATUTS_WORKFLOW
from utils.dashboard_services import get_dashboard_data
from utils.refero_services import get_refero_directions, get_refero_sites


def render_dashboard_page():
    st.title("📊 SURETIX - Tableau de Bord Sûreté")
    st.caption(
        "Indicateurs clés de performance (KPI) et pilotage des vulnérabilités"
    )

    df = get_dashboard_data()

    if df.empty:
        st.info("Aucune donnée d'incident disponible pour générer les KPI.")
        return

    # --- KPI HAUT DE PAGE ---
    col1, col2, col3, col4 = st.columns(4)

    total_incidents = len(df)
    nouveaux = len(df[df["statut"] == "nouveau"])
    en_cours = len(df[df["statut"].isin(["en_cours", "attente_prestataire"])])
    critiques = len(df[df["priorite"].isin(["critique", "haute"])])

    col1.metric("Total Incidents", total_incidents)
    col2.metric("Nouveaux (À traiter)", nouveaux, delta=f"{nouveaux} urgents")
    col3.metric("En cours de traitement", en_cours)
    col4.metric(
        "Niveau Priorité Haute/Critique", critiques, delta_color="inverse"
    )

    st.divider()

    # --- ANALYSE MULTIDIMENSIONNELLE ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📌 Répartition par Domaine Sûreté")
        domaine_counts = df["domaine"].value_counts()
        st.bar_chart(domaine_counts)

    with col_chart2:
        st.subheader("🔄 Répartition par Statut Workflow")
        # Cartographie des statuts lisibles
        df_statuts = df["statut"].map(
            lambda x: STATUTS_WORKFLOW.get(x.upper(), x)
        )
        st.bar_chart(df_statuts.value_counts())

    st.divider()

    # --- ANCRAGE REFERO : SITES & DIRECTIONS ---
    col_ref1, col_ref2 = st.columns(2)

    sites = get_refero_sites()
    sites_dict = {s["id"]: s["nom_site"] for s in sites} if sites else {}

    directions = get_refero_directions()
    dir_dict = (
        {d["id"]: d["sigle_direction"] for d in directions}
        if directions
        else {}
    )

    with col_ref1:
        st.subheader("🏢 Volume d'Incidents par Site (REFERO)")
        df["site_nom"] = df["refero_site_id"].map(
            lambda x: sites_dict.get(x, "Site inconnu")
        )
        st.bar_chart(df["site_nom"].value_counts())

    with col_ref2:
        st.subheader("🏛️ Demandes par Direction (REFERO)")
        df["direction_sigle"] = df["refero_direction_id"].map(
            lambda x: dir_dict.get(x, "Direction inconnue")
        )
        st.bar_chart(df["direction_sigle"].value_counts())