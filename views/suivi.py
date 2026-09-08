from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

from config import DOMAINES_SURETE, STATUTS_WORKFLOW, get_supabase_client
from utils.attachment_services import (
    delete_piece_jointe,
    get_pieces_jointes,
    upload_piece_jointe,
)
from utils.refero_services import get_refero_directions, get_refero_sites
from utils.relance_services import repousser_date_relance
from utils.suivi_services import (
    add_commentaire,
    get_commentaires,
    get_filtered_incidents,
    update_incident_statut,
)


def format_utc_to_local(iso_string: str) -> str:
    """Convertit un timestamp ISO UTC (Supabase) vers l'heure locale de Nouméa (UTC+11)."""
    if not iso_string:
        return "N/A"
    try:
        clean_iso = iso_string.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(clean_iso)
        dt_local = dt_utc.astimezone(ZoneInfo("Pacific/Noumea"))
        return dt_local.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        return iso_string[:16].replace("T", " ")


def render_suivi_page():
    st.title("📋 SURETIX - Suivi & Traitement des Incidents")

    # Récupération de l'utilisateur connecté en session
    user_profile = st.session_state.get("user_profile", {})
    user_email_actuel = user_profile.get("email") or user_profile.get("login") or "eric.kuter@gouv.nc"

    # --- ZONE DE FILTRES ---
    with st.expander("🔍 Filtres de recherche", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        sites = get_refero_sites()
        site_opts = {"Tous les sites": None}
        if sites:
            site_opts.update({s["nom_site"]: s["id"] for s in sites})

        directions = get_refero_directions()
        dir_opts = {"Toutes les directions": None}
        if directions:
            dir_opts.update(
                {d["sigle_direction"]: d["id"] for d in directions}
            )

        with col_f1:
            sel_site_label = st.selectbox("Site", list(site_opts.keys()))
        with col_f2:
            sel_dir_label = st.selectbox("Direction", list(dir_opts.keys()))
        with col_f3:
            sel_statut = st.selectbox(
                "Statut", ["Tous"] + list(STATUTS_WORKFLOW.values())
            )
        with col_f4:
            sel_domaine = st.selectbox(
                "Domaine Sûreté", ["Tous"] + DOMAINES_SURETE
            )

    site_id = site_opts[sel_site_label]
    dir_id = dir_opts[sel_dir_label]

    statut_key = "Tous"
    if sel_statut != "Tous":
        statut_key = [
            k for k, v in STATUTS_WORKFLOW.items() if v == sel_statut
        ][0]

    incidents = get_filtered_incidents(
        site_id, dir_id, statut_key, sel_domaine
    )

    if not incidents:
        st.info("Aucun incident ne correspond aux critères sélectionnés.")
        return

    # --- DISPOSITION DOUBLE COLONNE ---
    col_list, col_detail = st.columns([1, 1.2])

    with col_list:
        st.subheader(f"Tickets trouvés ({len(incidents)})")

        df = pd.DataFrame(incidents)

        selected_code = st.radio(
            "Sélectionner un ticket à traiter :",
            options=df["code_ticket"].tolist(),
            format_func=lambda x: f"{x} - {df[df['code_ticket']==x]['titre'].values[0]} [{df[df['code_ticket']==x]['statut'].values[0].upper()}]",
        )

    incident_sel = next(
        item for item in incidents if item["code_ticket"] == selected_code
    )

    with col_detail:
        st.subheader(f"Détail : {incident_sel['code_ticket']}")

        # Badges d'information
        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.metric("Priorité", incident_sel["priorite"].capitalize())
        col_b2.metric("Statut Actuel", incident_sel["statut"].upper())
        col_b3.metric("Domaine", incident_sel["domaine"])

        st.markdown(f"**Titre :** {incident_sel['titre']}")
        st.markdown(f"**Description :**\n> {incident_sel['description']}")
        st.caption(
            f"Demandeur : {incident_sel['demandeur_email']} | Équipement : {incident_sel.get('equipement_concerne') or 'N/A'}"
        )

        # --- GESTION SLA / DATE DE RELANCE ---
        st.divider()
        col_sla1, col_sla2 = st.columns([2, 1])
        date_rel_str = format_utc_to_local(incident_sel.get("date_relance"))
        col_sla1.info(f"⏳ **Prochaine échéance SLA :** {date_rel_str}")
        
        if col_sla2.button("🔄 Repousser SLA (+5j)", key=f"btn_rel_manual_{incident_sel['id']}"):
            repousser_date_relance(incident_sel["id"], jours=5)
            add_commentaire(
                incident_sel["id"],
                user_email_actuel,
                "Opération manuelle : Délai de relance repoussé de 5 jours.",
            )
            st.toast("Prochaine relance repoussée à +5 jours !", icon="✅")
            st.rerun()

        st.divider()

        # --- PIÈCES JOINTES & DOCUMENTS ---
        st.write("📎 **Pièces jointes & Documents**")
        pj_list = get_pieces_jointes(incident_sel["id"])

        if pj_list:
            for pj in pj_list:
                col_pj1, col_pj2, col_pj3 = st.columns([2.5, 1, 0.5])
                col_pj1.caption(f"📄 {pj['file_name']}")
                col_pj2.markdown(f"[📥 Ouvrir]({pj['file_path']})")

                if col_pj3.button(
                    "🗑️",
                    key=f"del_pj_{pj['id']}",
                    help="Supprimer définitivement la pièce jointe",
                ):
                    if delete_piece_jointe(pj["id"], pj["file_path"]):
                        st.toast("Pièce jointe supprimée !", icon="🗑️")
                        st.rerun()
        else:
            st.caption("Aucune pièce jointe liée à ce ticket.")

        with st.popover("➕ Ajouter un document / photo"):
            with st.form(
                key=f"form_pj_{incident_sel['id']}", clear_on_submit=True
            ):
                nouveau_fichier = st.file_uploader(
                    "Sélectionner un fichier",
                    type=["png", "jpg", "jpeg", "pdf"],
                    key=f"file_up_{incident_sel['id']}",
                )
                submit_pj = st.form_submit_button(
                    "Téléverser le fichier", use_container_width=True
                )

                if submit_pj:
                    if nouveau_fichier is not None:
                        with st.spinner("Envoi de la pièce jointe en cours..."):
                            res = upload_piece_jointe(
                                incident_sel["id"], nouveau_fichier
                            )
                            if res:
                                # Mise à jour de la date de relance lors d'un ajout de document
                                repousser_date_relance(incident_sel["id"], jours=5)
                                st.success("Fichier téléversé avec succès !")
                                st.rerun()
                    else:
                        st.warning("Veuillez d'abord sélectionner un fichier.")

        st.divider()

        # --- GESTION DU WORKFLOW ---
        st.write("🔄 **Changer le statut du ticket**")
        col_st1, col_st2 = st.columns([2, 1])

        options_statuts = list(STATUTS_WORKFLOW.keys())
        current_statut_upper = incident_sel["statut"].upper()
        default_index = (
            options_statuts.index(current_statut_upper)
            if current_statut_upper in options_statuts
            else 0
        )

        with col_st1:
            nouveau_statut = st.selectbox(
                "Nouveau Statut",
                options=options_statuts,
                index=default_index,
                format_func=lambda x: STATUTS_WORKFLOW[x],
                key=f"statut_select_{incident_sel['id']}",
            )
        with col_st2:
            st.write("")
            st.write("")
            if st.button("Mettre à jour", use_container_width=True):
                if nouveau_statut.lower() != incident_sel["statut"]:
                    update_incident_statut(incident_sel["id"], nouveau_statut)
                    add_commentaire(
                        incident_sel["id"],
                        user_email_actuel,
                        f"Changement de statut vers : {STATUTS_WORKFLOW[nouveau_statut]}",
                        changement_statut=nouveau_statut,
                    )
                    # Réinitialisation automatique du délai SLA (+5 jours)
                    repousser_date_relance(incident_sel["id"], jours=5)
                    st.success("Statut mis à jour et délai SLA relancé !")
                    st.rerun()

        st.divider()

        # --- MAIN COURANTE / COMMENTAIRES ---
        st.write("💬 **Main courante & Historique d'intervention**")

        commentaires = get_commentaires(incident_sel["id"])
        if commentaires:
            for com in commentaires:
                date_locale = format_utc_to_local(com["created_at"])
                with st.chat_message(
                    "user" if not com.get("changement_statut") else "assistant"
                ):
                    st.write(
                        f"**{com['auteur_email']}** — *{date_locale}*"
                    )
                    st.write(com["message"])
        else:
            st.caption("Aucune note enregistrée sur ce ticket.")

        with st.form(f"form_com_{incident_sel['id']}", clear_on_submit=True):
            auteur = st.text_input(
                "Votre Email / Identifiant", value=user_email_actuel
            )
            message = st.text_area(
                "Ajouter une note d'intervention (ex: Appel technicien, pièce commandée)",
                height=80,
            )
            btn_com = st.form_submit_button("Ajouter à la main courante")

            if btn_com and message:
                add_commentaire(incident_sel["id"], auteur, message)
                # Réinitialisation automatique du délai SLA (+5 jours)
                repousser_date_relance(incident_sel["id"], jours=5)
                st.success("Note ajoutée et délai de relance réinitialisé à +5 jours !")
                st.rerun()