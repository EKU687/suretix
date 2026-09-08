import streamlit as st
from config import get_supabase_client, TABLE_INCIDENTS, TABLE_COMMENTAIRES

supabase = get_supabase_client()

# utils/suivi_services.py

from config import get_supabase_client, TABLE_INCIDENTS

supabase = get_supabase_client()

from config import TABLE_INCIDENTS, get_supabase_client

supabase = get_supabase_client()


def get_filtered_incidents(
    site_id=None,
    direction_id=None,
    statut=None,
    domaine=None,
    inclure_archives=False,
):
    """Récupère les incidents en masquant uniquement les tickets clôturés de la vue active."""
    query = supabase.table(TABLE_INCIDENTS).select("*")

    if site_id:
        query = query.eq("refero_site_id", site_id)
    if direction_id:
        query = query.eq("refero_direction_id", direction_id)
    if domaine and domaine != "Tous":
        query = query.eq("domaine", domaine)

    # Filtrage selon le statut et l'archivage
    if statut and statut != "Tous":
        query = query.eq("statut", statut.lower())
    elif not inclure_archives:
        # Masque uniquement les tickets entièrement CLÔTURÉS
        query = query.neq("statut", "cloture")

    response = query.order("created_at", desc=True).execute()
    return response.data

def update_incident_statut(incident_id: str, nouveau_statut: str):
    """Met à jour le statut d'un ticket."""
    return supabase.table(TABLE_INCIDENTS).update({"statut": nouveau_statut.lower()}).eq("id", incident_id).execute()

def add_commentaire(incident_id: str, auteur_email: str, message: str, changement_statut: str = None):
    """Ajoute une entrée dans la main courante / historique du ticket."""
    payload = {
        "incident_id": incident_id,
        "auteur_email": auteur_email,
        "message": message,
        "changement_statut": changement_statut
    }
    return supabase.table(TABLE_COMMENTAIRES).insert(payload).execute()

def get_commentaires(incident_id: str):
    """Récupère l'historique des commentaires d'un incident."""
    return supabase.table(TABLE_COMMENTAIRES).select("*").eq("incident_id", incident_id).order("created_at", desc=False).execute().data