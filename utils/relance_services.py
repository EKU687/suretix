from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
from config import TABLE_INCIDENTS, get_supabase_client

supabase = get_supabase_client()
TZ_NC = ZoneInfo("Pacific/Noumea")


def get_incidents_a_relancer() -> list:
    """Récupère les incidents actifs dont la date de relance est dépassée (SLA > 5 jours)."""
    now_utc = datetime.now(ZoneInfo("UTC")).isoformat()

    try:
        res = (
            supabase.table(TABLE_INCIDENTS)
            .select("*")
            .not_.in_("statut", ["resolu", "cloture"])
            .lte("date_relance", now_utc)
            .order("date_relance", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Erreur lors de la vérification des relances : {e}")
        return []


def repousser_date_relance(incident_id: str, jours: int = 5) -> bool:
    """Repousse la date de relance d'un incident de X jours à compter d'aujourd'hui."""
    nouvelle_date = (datetime.now(ZoneInfo("UTC")) + timedelta(days=jours)).isoformat()
    try:
        supabase.table(TABLE_INCIDENTS).update(
            {"date_relance": nouvelle_date}
        ).eq("id", incident_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de la date de relance : {e}")
        return False