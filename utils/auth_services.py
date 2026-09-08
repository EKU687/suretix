import bcrypt
import streamlit as st
from config import get_supabase_client

supabase = get_supabase_client()


def verifier_mot_de_passe(mot_de_passe_saisi: str, mdp_stocke: str) -> bool:
    """Vérifie le mot de passe (hash bcrypt ou texte brut si BDD héritée)."""
    if not mdp_stocke:
        return False

    try:
        if mdp_stocke.startswith("$2b$") or mdp_stocke.startswith("$2a$"):
            return bcrypt.checkpw(
                mot_de_passe_saisi.encode("utf-8"), mdp_stocke.encode("utf-8")
            )
    except Exception:
        pass

    return mot_de_passe_saisi == mdp_stocke


def authentifier_utilisateur(login_ou_email: str, mot_de_passe: str) -> dict | None:
    """Authentifie l'agent via la table Utilisateur du PORTAIL-GNC."""
    identifiant = login_ou_email.strip().lower()

    try:
        res = (
            supabase.table("Utilisateur")
            .select(
                "id, login, nom, service, role, mdp, email,"
                " changement_mdp_requis, site_defaut"
            )
            .or_(f"login.eq.{identifiant},email.eq.{identifiant}")
            .execute()
        )

        users = res.data or []
        if not users:
            return None

        user = users[0]
        mdp_bd = user.get("mdp", "")

        if verifier_mot_de_passe(mot_de_passe, mdp_bd):
            nom_affiche = user.get("nom") or user.get("login") or "Agent"

            return {
                "id": user.get("id"),
                "login": user.get("login"),
                "email": user.get("email"),
                "full_name": nom_affiche.upper(),
                "service": user.get("service", "Sécurité"),
                "role": str(user.get("role", "agent")).lower().strip(),
                "site_defaut": user.get("site_defaut") or "DINUM",
                "changement_mdp_requis": user.get(
                    "changement_mdp_requis", False
                ),
            }

        return None

    except Exception as e:
        st.error(f"❌ Erreur BDD Authentification : {e}")
        return None


def render_login_screen():
    """Affiche le formulaire de connexion centralisé SURETIX / PORTAIL-GNC."""
    st.title("🛡️ SURETIX - Identification Agent")
    st.caption("Connexion requise pour accéder à la gestion des incidents de sûreté")

    col_center = st.columns([1, 2, 1])[1]

    with col_center:
        with st.form("form_login"):
            identifiant = st.text_input("Identifiant ou Email", placeholder="ex: e.kuter")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit:
                user_data = authentifier_utilisateur(identifiant, mot_de_passe)
                if user_data:
                    st.session_state["user"] = user_data
                    st.success(f"Bienvenue, {user_data['full_name']} !")
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")