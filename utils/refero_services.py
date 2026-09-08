import streamlit as st
from config import get_supabase_client

supabase = get_supabase_client()

@st.cache_data(ttl=3600)  # Cache de 1h pour les données référentielles
def get_refero_sites():
    """Récupère la liste des sites actifs."""
    response = (
        supabase.table("Sites")
        .select("id, nom_site, code_site, commune")
        .eq("actif", True)
        .order("nom_site")
        .execute()
    )
    return response.data

@st.cache_data(ttl=3600)
def get_refero_directions(site_id: str = None):
    """Récupère les directions actives (filtrées par site si renseigné)."""
    query = supabase.table("Directions").select("id, nom_direction, sigle_direction").eq("actif", True)
    if site_id:
        query = query.eq("id_site", site_id)
    response = query.order("sigle_direction").execute()
    return response.data

@st.cache_data(ttl=3600)
def get_refero_services(direction_id: str = None):
    """Récupère les services actifs (filtrés par direction si renseignée)."""
    query = supabase.table("Services").select("id, nom_service, sigle_service").eq("actif", True)
    if direction_id:
        query = query.eq("id_direction", direction_id)
    response = query.order("sigle_service").execute()
    return response.data