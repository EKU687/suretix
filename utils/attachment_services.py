import uuid
import streamlit as st
from config import TABLE_PIECES_JOINTES, get_supabase_client

supabase = get_supabase_client()
BUCKET_NAME = "suretix_attachments"


def upload_piece_jointe(incident_id: str, uploaded_file) -> dict:
    """Téléverse un fichier dans Supabase Storage et enregistre la référence en BDD."""
    try:
        file_extension = uploaded_file.name.split(".")[-1]
        unique_filename = f"{incident_id}/{uuid.uuid4().hex}.{file_extension}"

        # 1. Upload vers Supabase Storage
        file_bytes = uploaded_file.getvalue()
        supabase.storage.from_(BUCKET_NAME).upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": uploaded_file.type},
        )

        # 2. URL Publique
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(
            unique_filename
        )

        # 3. Insertion BDD
        payload = {
            "incident_id": incident_id,
            "file_path": file_url,
            "file_name": uploaded_file.name,
        }
        response = (
            supabase.table(TABLE_PIECES_JOINTES).insert(payload).execute()
        )
        return response.data

    except Exception as e:
        st.error(f"Échec du téléversement de la pièce jointe : {e}")
        return None


def get_pieces_jointes(incident_id: str) -> list:
    """Récupère la liste des pièces jointes associées à un incident."""
    response = (
        supabase.table(TABLE_PIECES_JOINTES)
        .select("*")
        .eq("incident_id", incident_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def delete_piece_jointe(pj_id: str, file_path: str) -> bool:
    """Supprime une pièce jointe du Storage Supabase et de la BDD PostgreSQL."""
    try:
        # 1. Extraction du chemin relatif du fichier dans le bucket
        storage_path = file_path.split(f"{BUCKET_NAME}/")[-1]

        # 2. Suppression dans le bucket Supabase Storage
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])

        # 3. Suppression dans la table suretix_pieces_jointes
        supabase.table(TABLE_PIECES_JOINTES).delete().eq("id", pj_id).execute()

        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la pièce jointe : {e}")
        return False