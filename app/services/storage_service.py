from uuid import uuid4
from datetime import datetime, timezone
from ..config import settings
from ..database import get_supabase

def upload_file(application_id: str, timeline_item_id: str, filename: str, content_type: str, data: bytes) -> dict:
    client = get_supabase()
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")[:120] or "attachment"
    path = f"{application_id}/{timeline_item_id}/{uuid4()}-{safe_name}"
    client.storage.from_(settings.supabase_storage_bucket).upload(
        path, data, {"content-type": content_type or "application/octet-stream", "upsert": "false"}
    )
    return {
        "id": str(uuid4()), "filename": filename, "storage_path": path,
        "content_type": content_type or "application/octet-stream",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

def signed_url(path: str) -> str:
    result = get_supabase().storage.from_(settings.supabase_storage_bucket).create_signed_url(path, 3600)
    return result.get("signedURL") or result.get("signedUrl") or ""

def remove_file(path: str) -> None:
    get_supabase().storage.from_(settings.supabase_storage_bucket).remove([path])
