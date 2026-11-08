# ApplySprint V1

ApplySprint turns university application information into an evidence-grounded checklist. It uses FastAPI, Supabase PostgreSQL/Storage, Groq, and a vanilla HTML/CSS/JS frontend.

## Features

- Application tickets for universities and programs.
- Optional admission URL and PDF upload.
- Groq-powered generation of 4–5 structured checklist items.
- Official, recommended, and unknown date labels.
- Persistent task completion and editable notes.
- Per-task document uploads to private Supabase Storage with signed download links.
- Retry timeline generation when source extraction or AI generation fails.
- Responsive dashboard and application workspace.

## 1. Requirements

- Python 3.12+
- A Supabase project
- A Groq API key

## 2. Supabase setup

1. Open your Supabase project and go to **SQL Editor**.
2. Run the complete contents of `sql/schema.sql`.
3. Confirm that the private Storage bucket `application-documents` exists.
4. Copy the Project URL and **service_role** key from Project Settings → API.

The API uses the service-role key server-side. Do not put it in frontend JavaScript or commit your `.env` file. V1 intentionally has no end-user authentication; the deployment is suitable for local development/private testing, not a public multi-user launch. Add Supabase Auth, owner IDs, and RLS before exposing it publicly.

## 3. Configure environment

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `GROQ_API_KEY`. You can change `GROQ_MODEL` to another model available to your Groq account that supports JSON mode.

## 4. Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/docs and health is at http://127.0.0.1:8000/health.

## 5. Workflow

1. Create an application using a program URL, optionally an admission URL and PDF.
2. The application record is saved first. The backend extracts readable page/PDF text and asks Groq for a validated JSON timeline.
3. If AI generation fails, the ticket remains available and the detail page offers **Generate / retry**.
4. Open a task to save notes or upload documents.
5. Completion and notes persist in Supabase.

## API

- `POST /api/applications` (multipart form; optional `admission_pdf`)
- `GET /api/applications`
- `GET /api/applications/{application_id}`
- `DELETE /api/applications/{application_id}`
- `POST /api/applications/{application_id}/generate-timeline`
- `GET /api/applications/{application_id}/timeline`
- `GET /api/timeline/{timeline_item_id}`
- `PATCH /api/timeline/{timeline_item_id}`
- `PUT /api/timeline/{timeline_item_id}/notes`
- `POST /api/timeline/{timeline_item_id}/attachments`
- `GET /api/timeline/{timeline_item_id}/attachments`
- `DELETE /api/attachments/{attachment_id}`

## Important implementation notes

- Website extraction is best-effort. JavaScript-rendered pages, login-gated content, bot protection, and inaccessible sites may not yield text. The UI lets you retry generation but does not claim that inaccessible pages were analyzed.
- PDF extraction uses text extraction; scanned/image-only PDFs need OCR and are not currently OCR-processed.
- LLM output is validated with Pydantic. Dates are nullable, and the prompt prohibits inventing official requirements or deadlines.
- The application deadline entered by the user is supplied to the model as user-provided context, not treated as a university-verified official date.
- Timeline regeneration does not overwrite an existing timeline. This intentionally protects notes and completion status; to change an existing generated checklist, edit items through the API or remove/recreate the application.
- Storage upload and database writes are separate operations. In case of an interrupted upload, an orphaned Storage object may need manual cleanup.
- No user authentication is included in V1. The service-role key bypasses RLS, so keep this app private until per-user authorization and ownership checks are implemented.
- URL extraction performs basic public-host checks to reduce SSRF risk. For a hardened public deployment, add redirect-by-redirect IP validation, strict egress controls, rate limiting, authentication, and file scanning.

## Project layout

```text
app/
  main.py
  config.py
  database.py
  schemas/
  routes/
  services/
  templates/
  static/css/
  static/js/
sql/schema.sql
.env.example
requirements.txt
README.md
```
