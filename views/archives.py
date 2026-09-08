# views/archives.py
import streamlit as st
import pandas as pd
from config import DOMAINES_SURETE, STATUTS_WORKFLOW
from utils.refero_services import get_refero_sites, get_refero_directions
from utils.suivi_services import get_filtered_incidents, get_commentaires
from views.suivi import format_utc_to_local

def render_archives_page():
    st.title("📂 SURETIX - Archives & Historique Sûreté")
    st.caption("Consultation des incidents résolus et clôturés (Registre réglementaire)")

    # Filtres spécifiques aux archives
    col_f1, col_f2, col_f3 = st.columns(3)
    
    sites = get_refero_sites()
    site_opts = {"Tous les sites": None}
    if sites:
        site_opts.update({s['nom_site']: s['id'] for s in sites})
        
    with col_f1:
        sel_site = st.selectbox("Site", list(site_opts.keys()))
    with col_f2:
        sel_statut = st.selectbox("Statut", ["Tous les archivés", "Résolu", "Clôturé"])
    with col_f3:
        sel_domaine = st.selectbox("Domaine Sûreté", ["Tous"] + DOMAINES_SURETE)

    # Inversion du filtre de statut
    statut_key = "Tous"
    if sel_statut == "Résolu":
        statut_key = "RESOLU"
    elif sel_statut == "Clôturé":
        statut_key = "CLOTURE"

    # Récupération en forçant le chargement des archives
    incidents = get_filtered_incidents(
        site_id=site_opts[sel_site], 
        statut=statut_key, 
        domaine=sel_domaine, 
        inclure_archives=True
    )

    # On ne conserve que les résolus/clôturés si "Tous les archivés" est sélectionné
    if sel_statut == "Tous les archivés":
        incidents = [i for i in incidents if i["statut"] in ["resolu", "cloture"]]

    if not incidents:
        st.info("Aucun incident archivé ne correspond aux critères.")
        return

    df = pd.DataFrame(incidents)
    
    # Export CSV pour le Registre Sûreté / Audits
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exporter l'historique en CSV",
        data=csv,
        file_name="suretix_archives.csv",
        mime="text/csv"
    )

    st.divider()

    # Affichage synthétique des archives
    for inc in incidents:
        with st.expander(f"📁 [{inc['code_ticket']}] {inc['titre']} - {inc['statut'].upper()} ({format_utc_to_local(inc['created_at'])})"):
            st.write(f"**Site / Direction :** {inc['refero_site_id']} / {inc['refero_direction_id']}")
            st.write(f"**Demandeur :** {inc['demandeur_email']}")
            st.write(f"**Description :** {inc['description']}")
            
            # Affichage de l'historique complet des interventions
            st.write("---")
            st.caption("Main courante d'intervention associée :")
            commentaires = get_commentaires(inc["id"])
            for com in commentaires:
                st.text(f"• [{format_utc_to_local(com['created_at'])}] {com['auteur_email']} : {com['message']}")