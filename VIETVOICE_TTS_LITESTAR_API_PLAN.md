# Minimal-Viable LiteStar API Plan for VietVoice-TTS

This document describes the **smallest possible HTTP interface** that turns Vietnamese text into speech using VietVoice-TTS.  It is designed as a *walking skeleton*: you can run it in a day, prove the library works behind an API, then iterate.

---
## 1. Project Overview
* **Objective** Expose a single REST endpoint that converts text → base64-encoded audio, plus a health probe.
* **Why minimal?** Shipping early gives you feedback on real deployment constraints and keeps maintenance cost low.

---
## 2. Flat Project Layout
```
vietvoicetts/
└── api/
    ├── __init__.py        # convenience import for "from vietvoicetts.api import app"
    ├── app.py            # Litestar ASGI instance & router registration
    ├── schemas.py        # ≤2 Pydantic models
    ├── handlers.py       # Endpoint functions
    └── tts_engine.py     # Thin async wrapper around VietVoice-TTS
```
*Rationale :* A deep tree (`routes/`, `services/`, `utils/`) only pays off once the codebase grows; keep everything close for now.

---
## 3. Endpoints
| Method | Path                | Purpose                      |
|--------|---------------------|------------------------------|
| POST   | `/api/v1/synthesize`| Convert text → base64 audio  |
| GET    | `/api/v1/health`    | Liveness & uptime check      |

### 3.1 `POST /api/v1/synthesize`
```json
Request
{
  "text": "Xin chào Việt Nam",
  "speed": 0.9,
  "output_format": "wav"
}

Response
{
  "audio_data": "<base64>",
  "duration": 1.23,
  "sample_rate": 24000,
  "format": "wav"
}
```

### 3.2 `GET /api/v1/health`
```json
{
  "status": "healthy",
  "uptime": 314
}
```

---
## 4. Pydantic Models (schemas.py)
```python
from pydantic import BaseModel, Field
from typing import Literal

class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    speed: float = Field(0.9, ge=0.1, le=3.0)
    output_format: Literal["wav", "mp3"] = "wav"

class SynthesizeResponse(BaseModel):
    audio_data: str         # base64 string
    duration: float         # seconds
    sample_rate: int        # Hz
    format: str             # "wav" | "mp3"
```

---
## 5. Dependencies
Minimal requirements (`requirements-api.txt`):
```
litestar[standard]>=2.0.0
uvicorn[standard]>=0.24.0
# VietVoice-TTS must already be installable (editable install recommended during dev)
```
Optional (only add when feature implemented): `python-multipart`, `redis`, `prometheus-client`, etc.

Install:
```bash
pip install -r requirements-api.txt
```

---
## 6. Application Bootstrap (app.py)
```python
from litestar import Litestar, post, get
from time import monotonic
from .schemas import SynthesizeRequest, SynthesizeResponse
from .tts_engine import synthesize_async

_started = monotonic()

@post("/api/v1/synthesize", response_model=SynthesizeResponse)
async def synthesize_handler(data: SynthesizeRequest) -> SynthesizeResponse:
    audio, sr, dur = await synthesize_async(data.text, data.speed, data.output_format)
    return SynthesizeResponse(
        audio_data=audio,
        duration=dur,
        sample_rate=sr,
        format=data.output_format,
    )

@get("/api/v1/health")
async def health_handler() -> dict[str, object]:
    return {"status": "healthy", "uptime": int(monotonic() - _started)}

app = Litestar([synthesize_handler, health_handler])
```
*The code above is illustrative; full implementation lives in the repository.*

---
## 7. Running Locally
```bash
uvicorn vietvoicetts.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Environment variable (optional):
```
VIETVOICE_TTS_MODEL=./models/base
```

---
## 8. Minimal Testing
Create `tests/test_api.py`:
```python
import base64, json, pytest, httpx

@pytest.mark.asyncio
async def test_synthesize():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        r = await client.post("/api/v1/synthesize", json={"text": "test"})
        assert r.status_code == 200
        data = r.json()
        base64.b64decode(data["audio_data"])  # should not raise
```
Run with `pytest -q` while the server is up.

---
## 9. Future Work – Path to Production-Grade
The following items can be added **incrementally** once the MVP is stable:
1. **File I/O** – `/synthesize/file` endpoint returning download URL; requires temporary storage & async file streaming.
2. **Voice Options & Cloning** – `/voices`, `/voices/clone` with multipart uploads.
3. **Structured Project Layout** – split `handlers.py` into `routes/`, move business logic to `services/`.
4. **Caching** – Redis cache keyed by normalized text + params to speed up repeated requests.
5. **Rate Limiting & Auth** – per-IP / API-key throttling using middleware.
6. **Observability** – Prometheus metrics, structured logging, OpenTelemetry traces.
7. **Docker & CI/CD** – containerize, add GitHub Actions pipeline, gunicorn with Uvicorn workers.
8. **Security Hardening** – CORS, content-type validation, file-size limits.
9. **Comprehensive Tests** – load, security, integration, mutation tests.
10. **Documentation** – polish OpenAPI descriptions, add usage guides and SDK generation.

Each bullet can be tackled independently without breaking existing clients, preserving the simplicity you ship today.
