"""
VietVoice-TTS API Module.

This module exposes the Litestar `app` object for serving with an ASGI server.
"""
from .app import app

__all__ = ["app"]