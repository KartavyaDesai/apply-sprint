from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import applications, timeline, attachments

app = FastAPI(title=settings.app_name, version="1.0.0", description="University application planning workspace")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(applications.router)
app.include_router(timeline.router)
app.include_router(attachments.router)

BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/")
def dashboard():
    return FileResponse(BASE / "templates" / "index.html")

@app.get("/applications/new")
def new_application():
    return FileResponse(BASE / "templates" / "create_application.html")

@app.get("/applications/{application_id}")
def application_detail(application_id: str):
    return FileResponse(BASE / "templates" / "application_detail.html")
