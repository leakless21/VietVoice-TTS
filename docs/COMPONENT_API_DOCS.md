# API Component Documentation

## Core Classes

- [`vietvoicetts/api/app.py`](vietvoicetts/api/app.py:27): Endpoint definitions
- [`vietvoicetts/api/tts_engine.py`](vietvoicetts/api/tts_engine.py:14): Engine wrapper
- [`vietvoicetts/api/schemas.py`](vietvoicetts/api/schemas.py:5): Request/response models

## Enum Definitions

- **Gender**: `"male"`, `"female"`
- **Group**: `"story"`, `"news"`, `"audiobook"`, `"interview"`, `"review"`
- **Area**: `"northern"`, `"southern"`, `"central"`
- **Emotion**: `"neutral"`, `"serious"`, `"monotone"`, `"sad"`, `"surprised"`, `"happy"`, `"angry"`

## Key Functionality

- Audio synthesis via `POST /synthesize`
- File generation via `POST /synthesize/file`
- File download via `GET /download/{id}`

## Limitations

- In-memory cache not persistent ([`vietvoicetts/api/app.py`](vietvoicetts/api/app.py:22))
- Thread-safety concerns with config changes ([`vietvoicetts/api/app.py`](vietvoicetts/api/app.py:52))
