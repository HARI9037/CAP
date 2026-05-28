import sys
import traceback

try:
    print("DEBUG: Checking imports...")
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from backend.app.memory.store import memory_store
    from backend.app.routes import chat, confirm, health, memory
    from backend.app.utils.env import Settings, initialize_settings
    from backend.app.utils.logging import configure_logging
except Exception:
    print("DEBUG: CRASH DURING IMPORT")
    traceback.print_exc()
    sys.exit(1)


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or initialize_settings()
    configure_logging(active_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime_settings = app.state.settings
        memory_store.initialize(
            db_path=runtime_settings.db_path,
            demo_mode=runtime_settings.demo_mode,
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
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def cap_debug_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-CAP-DEBUG"] = "active"
        return response

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(confirm.router)
    app.include_router(memory.router)

    return app


app = create_app()
