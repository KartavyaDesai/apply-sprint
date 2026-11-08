from datetime import datetime, timezone
from .source_extractor import extract_url, extract_pdf
from .timeline_agent import generate_timeline
from ..database import get_supabase

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def create_application(data: dict, pdf_bytes: bytes | None = None, pdf_name: str | None = None) -> dict:
    client = get_supabase()
    payload = {**data, "status": "active", "created_at": now_iso(), "updated_at": now_iso(), "source_documents": []}
    if pdf_bytes:
        # The source PDF is persisted in Storage and its reference is kept on the application.
        from ..config import settings
        from uuid import uuid4
        safe = "".join(c for c in (pdf_name or "admission-guidelines.pdf") if c.isalnum() or c in "._-")[:120]
        path = f"application-sources/{uuid4()}-{safe}"
        client.storage.from_(settings.supabase_storage_bucket).upload(
            path, pdf_bytes, {"content-type": "application/pdf", "upsert": "false"}
        )
        payload["source_documents"] = [{"filename": pdf_name or safe, "storage_path": path, "content_type": "application/pdf"}]
    result = client.table("applications").insert(payload).execute()
    application = result.data[0]
    try:
        generate_application_timeline(application, pdf_bytes)
        application["timeline_generation_status"] = "completed"
    except Exception as exc:
        # The ticket remains saved; generation can be retried.
        application["timeline_generation_status"] = "failed"
        application["timeline_generation_error"] = str(exc)[:500]
    return application

def generate_application_timeline(application: dict, pdf_bytes: bytes | None = None) -> list[dict]:
    texts, warnings = [], []
    for url in [application.get("program_url"), application.get("admission_url")]:
        text, warning = extract_url(url)
        if text:
            texts.append(f"SOURCE URL: {url}\n{text}")
        if warning:
            warnings.append(warning)
    if pdf_bytes:
        try:
            texts.append("UPLOADED ADMISSION PDF:\n" + extract_pdf(pdf_bytes))
        except Exception as exc:
            warnings.append(f"PDF extraction failed: {str(exc)[:180]}")
    source = "\n\n".join(texts)
    if not source.strip():
        source = "No source content could be retrieved. Use only the user's supplied application details and context. State clearly that university requirements could not be verified."
    if warnings:
        source += "\n\nSOURCE EXTRACTION WARNINGS:\n" + "\n".join(warnings)
    generated = generate_timeline(application, source)
    client = get_supabase()
    # Replace only the generated checklist. Notes and completion state on existing items are retained.
    existing = client.table("timeline_items").select("*").eq("application_id", application["id"]).order("sort_order").execute().data or []
    if existing:
        for item in existing:
            client.table("timeline_items").update({
                "title": item["title"], "description": item["description"],
                "due_date": item.get("due_date"), "is_completed": item.get("is_completed", False),
                "sort_order": item["sort_order"], "date_type": item.get("date_type", "unknown"),
                "source_reference": item.get("source_reference"), "updated_at": now_iso()
            }).eq("id", item["id"]).execute()
        return existing
    rows = []
    for index, item in enumerate(generated.items, 1):
        rows.append({
            "application_id": application["id"], **item.model_dump(mode="json"),
            "is_completed": False, "sort_order": index, "created_at": now_iso(), "updated_at": now_iso()
        })
    return client.table("timeline_items").insert(rows).execute().data
