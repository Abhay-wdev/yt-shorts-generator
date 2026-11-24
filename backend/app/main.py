import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import init_db
from .api.v1 import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("yt_shorts.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI YouTube Engagement Analyzer & Automatic Shorts Generator"
)

# CORS Middleware supporting any localhost or 127.0.0.1 port
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts for video previews and thumbnails
app.mount("/static/shorts", StaticFiles(directory=str(settings.DIR_SHORTS)), name="shorts")
app.mount("/static/thumbnails", StaticFiles(directory=str(settings.DIR_THUMBNAILS)), name="thumbnails")

# Mount API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing application...")
    settings.ensure_directories()
    init_db()
    
    # Clean up any leftover jobs from previous interrupted runs
    try:
        from .core.database import SessionLocal
        from .models.database import VideoAnalysisJob
        db = SessionLocal()
        stale_jobs = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.status.in_(["processing", "queued"])).all()
        for j in stale_jobs:
            j.status = "failed"
            j.error_message = "Interrupted by system restart. Ready to retry."
        db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"Could not clean up stale jobs: {e}")
        
    logger.info("AI YouTube Shorts Generator Backend is ready!")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
