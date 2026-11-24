from fastapi import APIRouter
from .system import router as system_router
from .channels import router as channels_router
from .videos import router as videos_router
from .analysis import router as analysis_router
from .engagement import router as engagement_router
from .shorts import router as shorts_router
from .publishing import router as publishing_router
from .analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(channels_router, prefix="/channels", tags=["YouTube Channels"])
api_router.include_router(videos_router, prefix="/videos", tags=["Source Videos"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Video Analysis"])
api_router.include_router(engagement_router, prefix="/engagement", tags=["Engagement Opportunities"])
api_router.include_router(shorts_router, prefix="/shorts", tags=["Shorts & Rendering"])
api_router.include_router(publishing_router, prefix="/publishing", tags=["Publishing Queue"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Performance & Learning"])
