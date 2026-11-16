from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.core.session_store import SessionStore
from app.services.model_adapter import LFM3Adapter


def get_session_store(
    request: Request,
) -> SessionStore:
    return request.app.state.session_store


def get_model_adapter(
    request: Request,
) -> LFM3Adapter:
    return request.app.state.model_adapter


def get_app_settings() -> Settings:
    return get_settings()


session_store_dependency = Depends(get_session_store)
model_adapter_dependency = Depends(get_model_adapter)
settings_dependency = Depends(get_app_settings)