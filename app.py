# =====================================================================
# APPLICATION PRINCIPALE : SURETIX (app.py)
# Gestion & Suivi des Incidents Sûreté sur sites sensibles GNC
# Entrée sécurisée par le Portail GNC (Jeton de Session)
# =====================================================================
from pathlib import Path
import sys

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# --- FIX DES CHEMINS PYTHON ---
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config import (
    APP_AUTHOR,
    APP_DATE,
    APP_ENV,
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
)
# 🛡️ IMPORT DU GARDE-FOU ET DE LA DÉCONNEXION PORTAIL
from utils.portal_guard import (
    deconnecter_et_retourner_portail,
    verifier_acces_depuis_portail,
)
from views.archives import render_archives_page
from views.dashboard import render_dashboard_page
from views.declaration import render_declaration_page
from views.suivi import render_suivi_page

# Ping automatique toutes les 3 minutes (180 000 ms) pour maintenir la session active
st_autorefresh(interval=180 * 1000, key="keep_alive_suretix")

# -----------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SURETIX - Incident Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 2. CONTRÔLE D'ENTRÉE STRICT PORTAIL GNC (GARDE-FOU)
# -----------------------------------------------------------------------------
user_info = verifier_acces_depuis_portail()
login_user = user_info.get("login")

# Stockage profil pour la traçabilité main courante
st.session_state["user_profile"] = {
    "full_name": user_info.get("nom", login_user),
    "role": str(user_info.get("role", "AGENT")).upper().strip(),
    "service": user_info.get("service", "Pôle Sûreté"),
    "login": login_user,
    "email": user_info.get("email", f"{login_user}@gouv.nc"),
}

user = st.session_state["user_profile"]

# -----------------------------------------------------------------------------
# 3. BARRE LATÉRALE & NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🛡️ **SURETIX**")

badge_env = "🟢 PROD" if APP_ENV == "PRODUCTION" else "🟠 BÊTA"

st.sidebar.caption(
    f"📋 **{APP_SUBTITLE}**\n\n"
    f"📌 Version : `{APP_VERSION}` | {badge_env}\n\n"
    f"📅 Mis à jour le : {APP_DATE}\n\n"
    f"👨‍💻 Auteur : **{APP_AUTHOR}**"
)
st.sidebar.markdown("---")

st.sidebar.markdown(f"👤 **{user['full_name']}**")
st.sidebar.caption(
    f"🏢 Service : **{user['service']}**\n\n"
    f"🔑 Rôle : `{user['role']}`"
)
st.sidebar.markdown("---")

options_menu = {
    "📊 Tableau de Bord": "dashboard",
    "🚨 Déclarer un Incident": "declaration",
    "📋 Suivi & Workflow": "suivi",
    "📂 Archives & Historique": "archives",
}

selection_label = st.sidebar.radio("Navigation", list(options_menu.keys()))
module_actif = options_menu[selection_label]

st.sidebar.divider()

# 🎯 BOUTON DE QUITTER / RETOUR PORTAIL GNC
if st.sidebar.button(
    "🏛️ Quitter & Retour au Portail",
    use_container_width=True,
    type="secondary",
):
    deconnecter_et_retourner_portail()

# -----------------------------------------------------------------------------
# 4. ROUTAGE DES VUES
# -----------------------------------------------------------------------------
if module_actif == "dashboard":
    render_dashboard_page()

elif module_actif == "declaration":
    render_declaration_page()

elif module_actif == "suivi":
    render_suivi_page()

elif module_actif == "archives":
    render_archives_page()