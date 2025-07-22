# vietvoicetts/api/tts_engine.py
import anyio
from anyio import to_thread
from vietvoicetts.client import TTSApi, ModelConfig
from loguru import logger

# --- Engine Initialization ---
# This is a crucial step. We create a single, long-lived engine instance
# when the application starts. This avoids the high cost of reloading the
# model on every API request.
_engine: TTSApi | None = None
_engine_config = ModelConfig()

def get_tts_engine() -> TTSApi:
    """
    Returns a lazily-initialized singleton of the TTS Engine.
    This prevents the model from loading until the first request.
    """
    global _engine
    if _engine is None:
        logger.info("Initializing TTS Engine for the first time...")
        try:
            # This is where the heavy model is loaded into memory.
            _engine = TTSApi(_engine_config)
            logger.info("TTS Engine initialized successfully.")
        except Exception as e:
            logger.error(f"Fatal error during TTS Engine initialization: {e}")
            raise RuntimeError(f"Could not initialize TTS Engine: {e}") from e
    return _engine

# --- Asynchronous Wrapper ---
from .schemas import Gender, Group, Area, Emotion

async def synthesize_async(
    text: str,
    speed: float,
    gender: Gender | None,
    group: Group | None,
    area: Area | None,
    emotion: Emotion | None,
) -> tuple[bytes, int, float]:
    """
    Asynchronously synthesizes text to audio bytes.

    This function wraps the synchronous `vietvoicetts` library call in a
    separate thread to avoid blocking the server's event loop.

    Args:
        text: The text to synthesize.
        speed: The desired speech speed.
        gender: Filter by voice gender.
        group: Filter by voice group.
        area: Filter by voice area.
        emotion: Filter by voice emotion.

    Returns:
        A tuple containing (audio_bytes, sample_rate, duration_seconds).
    """
    try:
        engine = get_tts_engine()
        
        # WARNING: This is not thread-safe. Modifying the config on the fly
        # will cause issues if you run more than one Uvicorn worker.
        # For a "walking skeleton," this is acceptable. For production, you
        # would need a more sophisticated engine management strategy.
        original_speed = engine.config.speed
        engine.config.speed = speed

        # The `run_sync` function takes our blocking `synthesize_to_bytes` call
        # and runs it in a background thread, awaiting the result.
        result = await to_thread.run_sync(
            engine.synthesize_to_bytes,
            text,
            gender.value if gender else None,
            group.value if group else None,
            area.value if area else None,
            emotion.value if emotion else None,
        )
        audio_bytes, _ = result

        # Restore the original speed for the next request.
        engine.config.speed = original_speed
        
        sample_rate = engine.config.sample_rate
        # For 16-bit PCM WAV audio, each sample is 2 bytes.
        duration_seconds = len(audio_bytes) / (sample_rate * 2)

        return audio_bytes, sample_rate, duration_seconds

    except Exception as e:
        logger.error(f"Error during synthesis: {e}")
        # Re-raise as a standard exception to be handled by the API framework.
        raise e