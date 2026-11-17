from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_health import router as health_router
from app.api.routes_turn import router as turn_router
from app.config import get_settings
from app.core.errors import AppError, ModelServerError
from app.core.session_store import SessionStore
from app.services.model_adapter import LFM3Adapter

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.settings = settings
    app.state.session_store = SessionStore(
        max_history_turns=settings.max_history_turns,
    )
    app.state.model_adapter = LFM3Adapter(
        base_url=settings.llama_cpp_server_url,
        timeout_seconds=settings.request_timeout_seconds,
    )

    yield

    app.state.session_store = None
    app.state.model_adapter = None


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ModelServerError)
    async def model_server_error_handler(
        request: Request,
        exc: ModelServerError,
    ):
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    app.include_router(health_router)
    app.include_router(turn_router)

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

    return app


app = create_app()