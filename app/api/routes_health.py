import shutil

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_app_settings

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health(
    settings: Settings = Depends(get_app_settings),
):
    ffmpeg_available = shutil.which("ffmpeg") is not None

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "model_id": settings.model_id,
        "model_server": settings.llama_cpp_server_url,
        "model_loaded": False,
        "ffmpeg_available": ffmpeg_available,
    }