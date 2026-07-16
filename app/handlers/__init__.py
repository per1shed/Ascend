from aiogram import Router

from app.handlers.admin import router as admin_router
from app.handlers.evening import router as evening_router
from app.handlers.fallback import router as fallback_router
from app.handlers.rest import router as rest_router
from app.handlers.settings import router as settings_router
from app.handlers.start import router as start_router
from app.handlers.stats import router as stats_router
from app.handlers.today import router as today_router


def setup_routers() -> Router:
    root = Router(name="root")
    root.include_router(start_router)
    root.include_router(today_router)
    root.include_router(rest_router)
    root.include_router(stats_router)
    root.include_router(settings_router)
    root.include_router(evening_router)
    root.include_router(admin_router)
    root.include_router(fallback_router)
    return root
