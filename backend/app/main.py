import importlib
import asyncio
import sys
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routers import search, export, auth
from app.dependencies import require_auth
from app.config import settings

# Windows-specific event loop fix - MUST BE AT TOP LEVEL
if sys.platform == "win32":
    # Use ProactorEventLoop for Python 3.8+
    if sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        # For older Python versions
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import the import module using importlib to avoid keyword conflict
import_module = importlib.import_module('app.routers.import')

app = FastAPI(title="Web Scraper & Outreach Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Static files are served by the frontend (Next.js) application
# app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(search.router, prefix="/api/search", dependencies=[Depends(require_auth)])
app.include_router(import_module.router, prefix="/api/import", dependencies=[Depends(require_auth)])
app.include_router(export.router, prefix="/api/export", dependencies=[Depends(require_auth)])

@app.get("/")
async def root():
    return {"message": "Web Scraper & Outreach Tool"}

@app.get("/login")
async def login_page():
    """Login endpoint - frontend handles the UI"""
    return {"message": "Please use the frontend application for login"}