import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from .config import settings
from .database import engine, Base, SessionLocal
from .models import *
from .routes import (
    auth_router,
    customers_router,
    invoices_router,
    payments_router,
    reconciliation_router,
    dashboard_router,
    reports_router,
    simulator_router,
    products_router,
    cheques_router
)
from .seeder import seed_demo_data

# Create DB Tables
Base.metadata.create_all(bind=engine)

# Seed initial demo data
with SessionLocal() as db_session:
    seed_demo_data(db_session)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered Financial Intelligence & Payment Reconciliation Platform"
)

# Enable CORS for local development and cross-origin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(invoices_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(reconciliation_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(simulator_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(cheques_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "database": "SQLite (Local) / PostgreSQL Ready"
    }

# Frontend Static Serving
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")
    app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
    app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")

    # Serve HTML pages directly
    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/{page_name}.html")
    def serve_html_page(page_name: str):
        page_file = frontend_dir / f"{page_name}.html"
        if page_file.exists():
            return FileResponse(page_file)
        return RedirectResponse(url="/")
