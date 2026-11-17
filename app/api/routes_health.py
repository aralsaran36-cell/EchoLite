import asyncio
import shutil
import urllib.request

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_app_settings

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


def _model_server_ready(base_url: str) -> bool:
    try:
        url = base_url.rstrip("/") + "/health"
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


@router.get("")
async def health(
    settings: Settings = Depends(get_app_settings),
):
    ffmpeg_available = shutil.which("ffmpeg") is not None
    model_loaded = await asyncio.to_thread(
        _model_server_ready, settings.llama_cpp_server_url
    )

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "model_id": settings.model_id,
        "model_server": settings.llama_cpp_server_url,
        "model_loaded": model_loaded,
        "ffmpeg_available": ffmpeg_available,
    }