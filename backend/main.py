from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.memory.store import memory_store
    from backend.app.routes import chat, confirm, health, memory
    from backend.app.utils.env import Settings, initialize_settings
except ModuleNotFoundError:
    from app.memory.store import memory_store
    from app.routes import chat, confirm, health, memory
    from app.utils.env import Settings, initialize_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or initialize_settings()

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings

    memory_store.initialize(
        db_path=settings.db_path,
        demo_mode=settings.demo_mode,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(confirm.router)
    app.include_router(memory.router)

    return app


app = create_app()
