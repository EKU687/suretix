import pandas as pd
from config import TABLE_INCIDENTS, get_supabase_client

supabase = get_supabase_client()


def get_dashboard_data():
    """Récupère l'ensemble des incidents pour analyse statistique."""
    response = (
        supabase.table(TABLE_INCIDENTS)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    # Nettoyage et conversion de dates pour agrégation temporelle
    df["created_at_dt"] = pd.to_datetime(df["created_at"])
    df["date_jour"] = df["created_at_dt"].dt.date
    return df