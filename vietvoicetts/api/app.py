import aiofiles
import os
import time
from litestar import Litestar, get, post
from litestar.response import Stream, File
from litestar.exceptions import NotFoundException
from litestar.background_tasks import BackgroundTask
from time import monotonic
from uuid import uuid4
from pathlib import Path
import tempfile
from typing import Dict, Any
from .settings import settings
from loguru import logger
from .schemas import HealthResponse, SynthesizeRequest, SynthesizeFileResponse
from .tts_engine import synthesize_async

# --- Application State ---
# Create a temporary directory for audio files that is cleaned up on system reboot.
TMP_DIR = settings.TMP_DIR_PATH 
TMP_DIR.mkdir(exist_ok=True)

FILE_LIFESPAN = settings.FILE_LIFESPAN_SECONDS 

# WARNING: This in-memory cache is not persistent and will be lost on restart.
# It is suitable for a "walking skeleton" but should be replaced with a
# persistent solution like Redis for production.
_file_cache: Dict[str, Dict[str, Any]] = {}

# --- Application State ---
_server_start_time = monotonic()

# --- API Endpoints ---
@get("/api/v1/health", summary="Check Service Health")
async def health() -> HealthResponse:
    """Provides a simple health check for load balancers and monitoring systems."""
    uptime = int(monotonic() - _server_start_time)
    return HealthResponse(status="healthy", uptime=uptime)

@post("/api/v1/synthesize", summary="Stream Audio Bytes")
async def synthesize_stream(data: SynthesizeRequest) -> Stream:
    """
    Synthesizes text and streams the audio bytes directly back to the client.
    This is efficient for short audio clips that can be played immediately.
    """
    audio_bytes, _, _ = await synthesize_async(
        text=data.text,
        speed=data.speed,
        gender=data.gender,
        group=data.group,
        area=data.area,
        emotion=data.emotion,
    )
    
    return Stream(
        content=iter([audio_bytes]),
        media_type=f"audio/{data.output_format}",
        headers={
            "Content-Disposition": f'inline; filename="speech.{data.output_format}"'
        },
    )


@post("/api/v1/synthesize/file", summary="Generate a Downloadable Audio File")
async def synthesize_to_file(data: SynthesizeRequest) -> SynthesizeFileResponse:
    """
    Synthesizes text, saves it to a temporary file, and returns a URL to download it.
    """
    audio_bytes, sr, dur = await synthesize_async(
        text=data.text,
        speed=data.speed,
        gender=data.gender,
        group=data.group,
        area=data.area,
        emotion=data.emotion,
    )
    
    file_id = uuid4().hex[:10]  # A unique ID for our file
    file_path = TMP_DIR / f"{file_id}.{data.output_format}"
    
    # Asynchronously write the audio bytes to the file to avoid blocking.
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(audio_bytes)
        
    file_size = len(audio_bytes)
    
    # Store the file's information in our temporary cache.
    _file_cache[file_id] = {"path": file_path, "format": data.output_format}
    
    return SynthesizeFileResponse(
        download_url=f"/api/v1/download/{file_id}",
        duration_seconds=round(dur, 2),
        sample_rate=sr,
        format=data.output_format,
        file_size_bytes=file_size,
    )

@get("/api/v1/download/{file_id:str}", summary="Download a Generated Audio File")
async def download_file(file_id: str) -> File:
    """
    Streams a previously generated audio file from the server to the client.
    """
    cached_file = _file_cache.get(file_id)
    if not cached_file or not cached_file["path"].exists():
        # If the ID is not in our cache or the file was deleted, return an error.
        raise NotFoundException(detail=f"File with ID '{file_id}' not found or has expired.")
        
    return File(
        path=cached_file["path"],
        media_type=f"audio/{cached_file['format']}",
        filename=f"speech_{file_id}.{cached_file['format']}",
        content_disposition_type="attachment", # Prompt user to save the file
    )

@post("/api/v1/synthesize/download", summary="Synthesize and Download Audio File Directly")
async def synthesize_and_download(data: SynthesizeRequest) -> Stream:
    """
    Synthesizes text and streams the audio back as a file attachment.
    This is the simplest method for scripts and direct downloads.
    """
    audio_bytes, _, _ = await synthesize_async(
        text=data.text,
        speed=data.speed,
        gender=data.gender,
        group=data.group,
        area=data.area,
        emotion=data.emotion,
    )


    cleanup_task = BackgroundTask(cleanup_old_files, TMP_DIR)
    
    # The only difference from the other streaming endpoint is the header.
    # 'attachment' tells the client (like a browser) to save the file
    # instead of trying to play it.
    return Stream(
        content=iter([audio_bytes]),
        media_type=f"audio/{data.output_format}",
        headers={"Content-Disposition": 'attachment; filename="synthesis_result.wav"'},
        background=cleanup_task
    )

async def cleanup_old_files(directory: Path):
    """Scans a directory and deletes files older than FILE_LIFESPAN_SECONDS."""
    logger.info(f"Running cleanup task on directory: {directory}")
    now = time.time()
    for filename in os.listdir(directory):
        file_path = directory / filename
        if os.path.isfile(file_path):
            try:
                if now - os.path.getmtime(file_path) > FILE_LIFESPAN:
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {file_path}")
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Error deleting file {file_path}: {e}")

# --- Litestar App Instance ---
# We must add our new endpoint function to the list!
app = Litestar(
    route_handlers=[health, synthesize_stream, synthesize_to_file, download_file, synthesize_and_download],
)