from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.memory.store import memory_store
from app.routes import chat, confirm, health, memory
from app.utils.env import Settings, get_settings
from app.utils.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        memory_store.initialize(
            db_path=active_settings.db_path,
            demo_mode=active_settings.demo_mode,
        )
        yield

    app = FastAPI(
        title=active_settings.app_name,
        version=active_settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(confirm.router)
    app.include_router(memory.router)
    return app


app = create_app()
