from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import database connection and initialize tables on startup
import app.database.connection as db
from app.core.config import uploads_dir, repo_root
from app.api.router import api_router

# Initialize database tables on startup
db.init_db()

app = FastAPI(title="Poultry AI API", version="1.0")

# Static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# CORSMiddleware configuration (allow_credentials=False for wildcard support)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the modular API routers
app.include_router(api_router, prefix="/api")

# Serve frontend SPA static files if the dist folder exists
dist_dir = repo_root / "poutry_ai" / "dist"

@app.get("/{catchall:path}")
def serve_spa(request: Request, catchall: str):
    # Ignore API and Uploads requests in catch-all
    if catchall.startswith("api") or catchall.startswith("uploads"):
        raise HTTPException(status_code=404, detail="Not Found")
        
    # If the file exists in the dist directory (like assets/index.js), serve it
    file_path = dist_dir / catchall
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # Fallback to index.html for React Router routing
    index_file = dist_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
        
    raise HTTPException(status_code=404, detail="Not Found")
