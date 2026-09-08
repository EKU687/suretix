import pandas as pd
import streamlit as st
from config import DOMAINES_SURETE, STATUTS_WORKFLOW
from utils.dashboard_services import get_dashboard_data
from utils.refero_services import get_refero_directions, get_refero_sites
from utils.relance_services import get_incidents_a_relancer, repousser_date_relance


def render_dashboard_page():
    st.title("📊 SURETIX - Tableau de Bord Sûreté")
    st.caption(
        "Indicateurs clés de performance (KPI), suivi des SLA et pilotage des vulnérabilités"
    )

    df = get_dashboard_data()

    if df.empty:
        st.info("Aucune donnée d'incident disponible pour générer les KPI.")
        return

    # --- CALCUL DES INCIDENTS EN SOUFFRANCE (> 5 JOURS) ---
    incidents_souffrance = get_incidents_a_relancer()
    nb_relances = len(incidents_souffrance)

    # --- KPI HAUT DE PAGE (5 COLONNES) ---
    col1, col2, col3, col4, col5 = st.columns(5)

    total_incidents = len(df)
    nouveaux = len(df[df["statut"] == "nouveau"])
    en_cours = len(df[df["statut"].isin(["en_cours", "attente_prestataire"])])
    critiques = len(df[df["priorite"].isin(["critique", "haute"])])

    col1.metric("Total Incidents", total_incidents)
    col2.metric("Nouveaux", nouveaux, delta=f"{nouveaux} à traiter")
    col3.metric("En cours", en_cours)
    col4.metric("Priorité Critique/Haute", critiques, delta_color="inverse")
    col5.metric(
        "Inactifs (> 5j)",
        nb_relances,
        delta=f"{nb_relances} en souffrance" if nb_relances > 0 else "À jour",
        delta_color="inverse",
    )

    st.divider()

    # --- FOCUS SLA : TICKETS EN SOUFFRANCE ET ALERTS DE RELANCE ---
    if incidents_souffrance:
        st.subheader("🚨 Incidents en Souffrance (SLA > 5 jours)")
        st.caption("Tickets actifs sans mise à jour ou action enregistrée depuis au moins 5 jours.")

        df_relance = pd.DataFrame(incidents_souffrance)
        
        for idx, row in df_relance.iterrows():
            col_rel1, col_rel2, col_rel3 = st.columns([3, 1.5, 1])
            
            statut_traduit = STATUTS_WORKFLOW.get(str(row.get("statut")).upper(), row.get("statut"))
            col_rel1.warning(
                f"**{row.get('code_ticket')}** - {row.get('titre')} "
                f"*(Statut : {statut_traduit} | Priorité : {str(row.get('priorite')).upper()})*"
            )
            col_rel2.caption(f"Demandeur : {row.get('demandeur_email')}")
            
            # Bouton de relance rapide (+5 jours)
            if col_rel3.button("🔄 Relancer +5j", key=f"btn_rel_{row.get('id')}"):
                if repousser_date_relance(row.get("id"), jours=5):
                    st.toast(f"Délai réinitialisé pour {row.get('code_ticket')}", icon="✅")
                    st.rerun()

        st.divider()

    # --- ANALYSE MULTIDIMENSIONNELLE ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📌 Répartition par Domaine Sûreté")
        domaine_counts = df["domaine"].value_counts()
        st.bar_chart(domaine_counts)

    with col_chart2:
        st.subheader("🔄 Répartition par Statut Workflow")
        df_statuts = df["statut"].map(
            lambda x: STATUTS_WORKFLOW.get(str(x).upper(), x)
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