import os
from supabase import Client, create_client

# =========================================================================
# APPLICATION CONFIGURATION & VERSIONING (config.py)
# Système SURETIX - Gouvernement de la Nouvelle-Calédonie
# =========================================================================

# 🎯 Semantic Versioning (SemVer) : MAJOR.MINOR.PATCH
APP_VERSION = "1.0.0"
APP_DATE = "08/09/2026"
APP_ENV = "PRODUCTION"  # "DEVELOPMENT" ou "PRODUCTION"

APP_NAME = "SURETIX"
APP_SUBTITLE = "Gestion & Suivi des Incidents Sûreté"
APP_AUTHOR = "Éric KUTER"


# =========================================================================
# 🗝️ CONFIGURATION ET CLIENT SUPABASE
# =========================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "TA_CLE_URL_SUPABASE")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "TA_CLE_ANON_SUPABASE")


def get_supabase_client() -> Client:
    """Initialise et retourne le client unique Supabase."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================================
# 🗄️ NOMS DES TABLES POSTGRESQL (Convention suretix_)
# =========================================================================
TABLE_INCIDENTS = "suretix_incidents"
TABLE_COMMENTAIRES = "suretix_commentaires"
TABLE_PIECES_JOINTES = "suretix_pieces_jointes"


# =========================================================================
# 🛡️ RÉFÉRENTIELS ET WORKFLOWS MÉTIER SÛRETÉ
# =========================================================================
DOMAINES_SURETE = [
    "Contrôle d'Accès",
    "Vidéo-protection (CCTV)",
    "Anti-intrusion / Alarme",
    "Sécurité Physique / Clôture",
    "Incendie / SSI",
    "Incidents Humains / Incivilités",
    "Autre",
]

STATUTS_WORKFLOW = {
    "NOUVEAU": "Nouveau",
    "EN_COURS": "En cours de traitement",
    "ATTENTE_PRESTATAIRE": "En attente prestataire",
    "RESOLU": "Résolu",
    "CLOTURE": "Clôturé",
}

NIVEAUX_PRIORITE = ["Faible", "Moyenne", "Haute", "Critique"]