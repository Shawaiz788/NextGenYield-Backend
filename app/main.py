from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os

from app.config import settings
from app.database import engine, Base
from app.routers import auth, fields, crop_cycles, observations, advisory

# Initialize database schema tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NextGenYield: Wheat Crop Decision Support and Vision AI System Backend. Aligned with F26-201 and PostgreSQL / Supabase schema.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for React Native / Expo development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(fields.router, prefix=settings.API_V1_STR)
app.include_router(crop_cycles.router, prefix=settings.API_V1_STR)
app.include_router(observations.router, prefix=settings.API_V1_STR)
app.include_router(advisory.router, prefix=settings.API_V1_STR)
app.include_router(advisory.showcase_router, prefix=settings.API_V1_STR)

# Static file serving for local fallback storage
LOCAL_UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
@app.get(f"{settings.API_V1_STR}/storage/file/{{filename}}", tags=["Storage"])
def serve_uploaded_file(filename: str):
    file_path = os.path.join(LOCAL_UPLOADS_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"message": "File not found"})
    return FileResponse(file_path)

@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": "connected",
        "supabase_configured": bool(settings.SUPABASE_URL and "your-project" not in settings.SUPABASE_URL),
        "ai_service_gateway": settings.AI_INFERENCE_SERVICE_URL,
    }

