from contextlib import asynccontextmanager


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi.staticfiles import StaticFiles
from app.api.routes_health import router as health_router
from app.api.routes_turn import router as turn_router

from app.config import Settings, get_settings
from app.core.errors import AppError
from app.core.session_store import SessionStore
from app.services.model_adapter import LFM3Adapter


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.settings = settings
    app.state.session_store = SessionStore(
        max_history_turns=settings.max_history_turns,
    )
    app.state.model_adapter = LFM3Adapter(
        base_url=settings.llama_cpp_server_url,
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

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ):
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
            },
        )

    app.include_router(health_router)
    app.include_router(turn_router)

    app.mount(
        "/static",
        StaticFiles(directory="app/static"),
        name="static",
    )

    return app


app = create_app()