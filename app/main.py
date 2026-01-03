from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth
import os
from app.core.config import get_settings
from app.api.endpoints import auth, receipts,tags,reports

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Masjid Receipts API",
    description="Receipt management system for mosque finances",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)
# Include receipts router
app.include_router(
    receipts.router,
    prefix="/api/receipts",
    tags=["Receipts"]
)
# Include tags router
app.include_router(
    tags.router,
    prefix="/api/tags",
    tags=["Tags"]
)

# Include reports router
app.include_router(
    reports.router,
    prefix="/api/reports",
    tags=["Reports"]
)

@app.get("/")
def read_root():
    return {
        "message": "Masjid Receipts API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }



@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"API started successfully")
    print(f"API Documentation: http://localhost:8000/docs")