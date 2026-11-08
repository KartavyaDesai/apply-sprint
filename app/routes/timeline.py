from fastapi import APIRouter, HTTPException
from ..database import get_supabase
from ..schemas.timeline import TimelinePatch, NotesUpdate
from ..services.application_service import now_iso

router = APIRouter(prefix="/api", tags=["timeline"])

@router.get("/applications/{application_id}/timeline")
def list_timeline(application_id: str):
    return get_supabase().table("timeline_items").select("*").eq("application_id", application_id).order("sort_order").execute().data or []

@router.get("/timeline/{timeline_item_id}")
def get_timeline_item(timeline_item_id: str):
    client = get_supabase()
    item = client.table("timeline_items").select("*").eq("id", timeline_item_id).maybe_single().execute().data
    if not item:
        raise HTTPException(404, "Timeline item not found")
    note = client.table("timeline_notes").select("*").eq("timeline_item_id", timeline_item_id).maybe_single().execute().data
    item["workspace"] = note or {"note": "", "attachments": []}
    return item

@router.patch("/timeline/{timeline_item_id}")
def patch_timeline_item(timeline_item_id: str, patch: TimelinePatch):
    values = patch.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(400, "No changes supplied")
    values["updated_at"] = now_iso()
    result = get_supabase().table("timeline_items").update(values).eq("id", timeline_item_id).execute()
    if not result.data:
        raise HTTPException(404, "Timeline item not found")
    return result.data[0]

@router.put("/timeline/{timeline_item_id}/notes")
def update_notes(timeline_item_id: str, payload: NotesUpdate):
    client = get_supabase()
    item = client.table("timeline_items").select("id").eq("id", timeline_item_id).maybe_single().execute().data
    if not item:
        raise HTTPException(404, "Timeline item not found")
    existing = client.table("timeline_notes").select("*").eq("timeline_item_id", timeline_item_id).maybe_single().execute().data
    values = {"note": payload.note, "updated_at": now_iso()}
    if existing:
        result = client.table("timeline_notes").update(values).eq("id", existing["id"]).execute()
    else:
        values.update({"timeline_item_id": timeline_item_id, "attachments": [], "created_at": now_iso()})
        result = client.table("timeline_notes").insert(values).execute()
    return result.data[0]
