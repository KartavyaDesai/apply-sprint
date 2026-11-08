from fastapi import APIRouter, UploadFile, File, HTTPException
from ..database import get_supabase
from ..config import settings
from ..services.storage_service import upload_file, signed_url, remove_file
from ..services.application_service import now_iso

router = APIRouter(prefix="/api", tags=["attachments"])
ALLOWED = {"application/pdf", "image/png", "image/jpeg", "text/plain",
           "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

def _note_for_item(client, item_id):
    item = client.table("timeline_items").select("id,application_id").eq("id", item_id).maybe_single().execute().data
    if not item:
        raise HTTPException(404, "Timeline item not found")
    note = client.table("timeline_notes").select("*").eq("timeline_item_id", item_id).maybe_single().execute().data
    if not note:
        note = client.table("timeline_notes").insert({
            "timeline_item_id": item_id, "note": None, "attachments": [],
            "created_at": now_iso(), "updated_at": now_iso()
        }).execute().data[0]
    return item, note

@router.post("/timeline/{timeline_item_id}/attachments")
async def add_attachment(timeline_item_id: str, file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(400, "File is empty")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Maximum upload size is {settings.max_upload_mb} MB")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED:
        raise HTTPException(415, "Unsupported file type")
    client = get_supabase()
    item, note = _note_for_item(client, timeline_item_id)
    metadata = upload_file(item["application_id"], timeline_item_id, file.filename or "attachment", content_type, content)
    attachments = (note.get("attachments") or []) + [metadata]
    result = client.table("timeline_notes").update({"attachments": attachments, "updated_at": now_iso()}).eq("id", note["id"]).execute()
    metadata["url"] = signed_url(metadata["storage_path"])
    return metadata

@router.get("/timeline/{timeline_item_id}/attachments")
def list_attachments(timeline_item_id: str):
    client = get_supabase()
    _, note = _note_for_item(client, timeline_item_id)
    result = []
    for attachment in note.get("attachments") or []:
        item = dict(attachment)
        item["url"] = signed_url(item["storage_path"])
        result.append(item)
    return result

@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: str):
    client = get_supabase()
    notes = client.table("timeline_notes").select("*").execute().data or []
    for note in notes:
        attachments = note.get("attachments") or []
        target = next((a for a in attachments if a.get("id") == attachment_id), None)
        if target:
            remove_file(target["storage_path"])
            remaining = [a for a in attachments if a.get("id") != attachment_id]
            client.table("timeline_notes").update({"attachments": remaining, "updated_at": now_iso()}).eq("id", note["id"]).execute()
            return {"deleted": True}
    raise HTTPException(404, "Attachment not found")
