# Architecture Design

## 1. Overview

This document outlines the architecture and design considerations for the VietVoice TTS application. The system is designed to be a flexible and extensible text-to-speech engine with a command-line interface (CLI) and a high-level Python client API.

## 2. Core Components

- **`vietvoicetts.core.tts_engine`**: The core component responsible for synthesizing speech from text.
- **`vietvoicetts.core.model`**: Manages the TTS model, including loading, inference, and voice selection.
- **`vietvoicetts.core.model_config`**: Defines the configuration for the TTS model and related parameters.
- **`vietvoicetts.cli`**: Provides a command-line interface for interacting with the TTS engine.
- **`vietvoicetts.client`**: Provides a high-level Python API for programmatic access to TTS features.
- **API Component (`vietvoicetts/api/app.py`, `vietvoicetts/api/tts_engine.py`)**: Exposes TTS functionality via HTTP endpoints for health checks, streaming synthesis, file-based synthesis, and file download.

## 3. Design for Default Settings

To accommodate configurable default settings, the following changes have been made:

- **`vietvoicetts/cli.py`**:
  - The `get_required_inputs` function uses a configurable default output folder.
  - The `get_default_settings` function sets the default gender and emotion.
- **`vietvoicetts/client.py`**:
  - The convenience functions `synthesize` and `synthesize_to_bytes` now default to "female" for gender and "neutral" for emotion if not explicitly provided.

This approach centralizes the default settings in both the CLI and client API, making them easy to manage and modify without affecting the core TTS engine.

## 4. Cache and Storage Strategy

- The API uses an in-memory cache (`_file_cache`) to store metadata and paths for generated audio files, enabling fast download and temporary persistence.
- For production, it is recommended to replace the in-memory cache with a persistent Redis cache to support multi-instance deployments and survive server restarts.
- Audio files are saved to disk in a configurable output directory. Temporary files should be periodically cleaned up by a background task.

## 5. Thread-Safety Limitations

- The TTS engine configuration is not thread-safe. Modifying the engine config (e.g., speech speed) on the fly can cause issues if multiple Uvicorn workers are used.
- For demonstration and development, this is acceptable. For production, a more robust engine management strategy is required to ensure thread/process safety.

## 6. Deployment Considerations

---

## 7. API Schema and Enum Parameter Flow

- The API schemas now use Python `Enum` classes for `gender`, `group`, `area`, and `emotion`.
- These enums are defined in [`vietvoicetts/api/schemas.py`](vietvoicetts/api/schemas.py:1) and are used throughout the API request/response cycle.
- The API handlers in [`vietvoicetts/api/app.py`](vietvoicetts/api/app.py:1) pass these enum values to the synthesis engine.
- The synthesis engine in [`vietvoicetts/api/tts_engine.py`](vietvoicetts/api/tts_engine.py:1) forwards these parameters to the core TTS API.
- This ensures type safety, better documentation, and easier client integration.

The application is deployed as a Python package and can be run directly from the command line or imported as a library. The changes to the default settings do not impact the deployment process.
