from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import ValidationError
from ..database import get_supabase
from ..schemas.application import ApplicationCreate
from ..services.application_service import create_application, generate_application_timeline

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.get("")
def list_applications():
    try:
        client = get_supabase()
        apps = client.table("applications").select("*").order("created_at", desc=True).execute().data or []
        for app in apps:
            items = client.table("timeline_items").select("id,is_completed").eq("application_id", app["id"]).execute().data or []
            app["timeline_total"] = len(items)
            app["timeline_completed"] = sum(1 for x in items if x["is_completed"])
        return apps
    except Exception as exc:
        raise HTTPException(503, str(exc))

@router.post("")
async def create_application_route(
    university_name: str = Form(...), program_name: str = Form(...), program_url: str = Form(...),
    admission_url: str | None = Form(None), application_deadline: str | None = Form(None),
    intake: str | None = Form(None), additional_context: str | None = Form(None),
    admission_pdf: UploadFile | None = File(None)
):
    try:
        data = ApplicationCreate.model_validate({
            "university_name": university_name, "program_name": program_name, "program_url": program_url,
            "admission_url": admission_url or None, "application_deadline": application_deadline or None,
            "intake": intake or None, "additional_context": additional_context or None
        }).model_dump(mode="json")
        pdf_bytes = await admission_pdf.read() if admission_pdf else None
        if pdf_bytes and len(pdf_bytes) > 15 * 1024 * 1024:
            raise HTTPException(413, "Admission PDF exceeds the 15 MB limit.")
        if pdf_bytes and admission_pdf.content_type not in {"application/pdf", "application/octet-stream"}:
            raise HTTPException(415, "Admission guideline must be a PDF.")
        return create_application(data, pdf_bytes, admission_pdf.filename if admission_pdf else None)
    except HTTPException:
        raise
    except (ValidationError, ValueError) as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(500, str(exc))

@router.get("/{application_id}")
def get_application(application_id: str):
    client = get_supabase()
    app = client.table("applications").select("*").eq("id", application_id).maybe_single().execute().data
    if not app:
        raise HTTPException(404, "Application not found")
    items = client.table("timeline_items").select("*").eq("application_id", application_id).order("sort_order").execute().data or []
    app["timeline_items"] = items
    app["timeline_total"] = len(items)
    app["timeline_completed"] = sum(1 for x in items if x["is_completed"])
    return app

@router.delete("/{application_id}")
def delete_application(application_id: str):
    result = get_supabase().table("applications").delete().eq("id", application_id).execute()
    return {"deleted": bool(result.data)}

@router.post("/{application_id}/generate-timeline")
def retry_generation(application_id: str):
    client = get_supabase()
    app = client.table("applications").select("*").eq("id", application_id).maybe_single().execute().data
    if not app:
        raise HTTPException(404, "Application not found")
    try:
        items = generate_application_timeline(app)
        return {"items": items, "status": "completed"}
    except Exception as exc:
        raise HTTPException(502, f"Timeline generation failed: {exc}")
