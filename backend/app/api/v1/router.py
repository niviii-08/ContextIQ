from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.interruptions import router as interruptions_router
from app.api.v1.locations import router as locations_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.recommendations import router as recommendations_router
# NEW — auth, notifications, system monitoring
from app.api.v1.auth import router as auth_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.system import router as system_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(interruptions_router)
api_router.include_router(locations_router)
api_router.include_router(analytics_router)
api_router.include_router(predictions_router)
api_router.include_router(recommendations_router)
api_router.include_router(notifications_router)
api_router.include_router(system_router)
