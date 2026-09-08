from datetime import datetime
import streamlit as st

from config import DOMAINES_SURETE, NIVEAUX_PRIORITE, TABLE_INCIDENTS, get_supabase_client
from utils.attachment_services import upload_piece_jointe
from utils.refero_services import (
    get_refero_directions,
    get_refero_services,
    get_refero_sites,
)


def render_declaration_page():
    st.title("🛡️ SURETIX - Déclaration d'Incident Sûreté")
    st.caption("Saisie d'un événement / dysfonctionnement sur un site sensible du GNC")

    supabase = get_supabase_client()

    # --- CHARGEMENT DYNAMIQUE REFERO ---
    sites = get_refero_sites()
    if not sites:
        st.warning("Aucun site actif trouvé dans REFERO.")
        return

    st.subheader("1. Localisation (REFERO)")
    site_options = {f"{s['nom_site']} ({s.get('commune', 'N/A')})": s['id'] for s in sites}
    selected_site_label = st.selectbox("Site concerné *", options=list(site_options.keys()))
    selected_site_id = site_options[selected_site_label]

    directions = get_refero_directions(selected_site_id)
    if not directions:
        directions = get_refero_directions()

    direction_options = {f"{d['sigle_direction']} - {d['nom_direction']}": d['id'] for d in directions}
    selected_direction_label = st.selectbox("Direction émettrice *", options=list(direction_options.keys()))
    selected_direction_id = direction_options[selected_direction_label]

    services = get_refero_services(selected_direction_id)
    service_options = {f"{s['sigle_service']} - {s['nom_service']}": s['id'] for s in services} if services else {}
    
    selected_service_id = None
    if service_options:
        selected_service_label = st.selectbox("Service émetteur", options=list(service_options.keys()))
        selected_service_id = service_options[selected_service_label]

    # --- FORMULAIRE DÉTAILS INCIDENT ---
    with st.form("form_nouveau_ticket", clear_on_submit=True):
        st.subheader("2. Qualification & Demandeur")
        
        col1, col2 = st.columns(2)
        with col1:
            demandeur_email = st.text_input("Email du demandeur *", placeholder="agent@gouv.nc")
            domaine = st.selectbox("Domaine Sûreté *", DOMAINES_SURETE)
        with col2:
            priorite = st.select_slider("Niveau d'urgence / Priorité", options=NIVEAUX_PRIORITE, value="Moyenne")
            equipement = st.text_input("Équipement impacté", placeholder="Ex: Caméra CAM-02 / Lecteur Porte 101")

        titre = st.text_input("Objet de la demande / Titre *", placeholder="Ex: Panne de lecture de badge d'accès")
        description = st.text_area("Description détaillée des faits *", height=120)

        # Ajout du champ pour pièce jointe
        piece_jointe = st.file_uploader(
            "📎 Pièce jointe / Photo (Optionnel)",
            type=["png", "jpg", "jpeg", "pdf"],
            help="Photos du dysfonctionnement, captures d'écran, devis...",
        )

        submitted = st.form_submit_button("🚨 Enregistrer la demande", use_container_width=True)

        # Traitement à la soumission (à l'intérieur du bloc form)
        if submitted:
            if not titre or not description or not demandeur_email:
                st.error("Veuillez renseigner tous les champs obligatoires (*).")
            else:
                code_ticket = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                payload = {
                    "code_ticket": code_ticket,
                    "refero_site_id": selected_site_id,
                    "refero_direction_id": selected_direction_id,
                    "refero_service_id": selected_service_id,
                    "demandeur_email": demandeur_email,
                    "domaine": domaine,
                    "equipement_concerne": equipement,
                    "priorite": priorite.lower(),
                    "titre": titre,
                    "description": description,
                    "statut": "nouveau"
                }

                try:
                    # 1. Enregistrement de l'incident
                    res = supabase.table(TABLE_INCIDENTS).insert(payload).execute()
                    new_incident_id = res.data[0]["id"]

                    # 2. Upload de la pièce jointe si présente
                    if piece_jointe is not None:
                        upload_piece_jointe(new_incident_id, piece_jointe)

                    st.success(f"Ticket enregistré sous la référence **{code_ticket}**")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement : {e}")