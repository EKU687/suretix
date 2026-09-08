# test_connection.py
import streamlit as st
from config import get_supabase_client, TABLE_INCIDENTS

st.title("Test de Connexion SURETIX - Supabase 🛡️")

supabase = get_supabase_client()

try:
    # Tentative de lecture sur la table
    response = supabase.table(TABLE_INCIDENTS).select("count", count="exact").execute()
    st.success(f"Connexion réussie à la table '{TABLE_INCIDENTS}' !")
    st.info(f"Nombre de tickets actuellement enregistrés : {response.count}")
except Exception as e:
    st.error(f"Échec de la connexion à la table '{TABLE_INCIDENTS}' : {e}")