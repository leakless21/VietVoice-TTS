# VietVoice-TTS Litestar API

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Framework](https://img.shields.io/badge/framework-Litestar-purple)
![License](https://img.shields.io/badge/license-MIT-green)

This repository contains a high-performance, asynchronous REST API for serving the [VietVoice-TTS](https://github.com/v-nhandt/VietVoice-TTS) model. It is built with the modern Litestar web framework to provide a fast, reliable, and easy-to-use interface for text-to-speech synthesis.

## Key Features

- **High-Performance & Asynchronous:** Built on Litestar and Uvicorn, capable of handling many concurrent requests without blocking.
- **Multiple Synthesis Patterns:**
  - **Direct Download:** A simple, one-step endpoint for scripts and direct file downloads.
  - **Inline Playback:** An endpoint designed for embedding audio directly in web applications.
  - **Asynchronous Job Pattern:** A two-step process to generate a file and provide a stable URL, ideal for long-running tasks and complex UIs.
- **Full Voice Customization:** Control the voice's `gender`, `area` (accent), `group`, and `emotion` through simple API parameters.
- **Robust and Self-Documenting:** Uses Pydantic for automatic request validation and can generate OpenAPI (Swagger/Redoc) documentation.
- **Production-Ready Design:** Includes patterns for configuration management, background tasks, and a clear path to production-grade features like caching and containerization.

## Technology Stack

- **Web Framework:** [Litestar](https://litestar.dev/)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/)
- **Core TTS Library:** [VietVoice-TTS](https://github.com/v-nhandt/VietVoice-TTS)

---

## Getting Started

Follow these instructions to get the API running on your local machine.

### 1. Prerequisites

- Python 3.10 or newer.
- [Git](https://git-scm.com/) for cloning the repository.
- It is highly recommended to use `uv` for fast dependency management.

  ```bash
  pip install uv
  ```

### 2. Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repository-url>
   cd <your-repository-directory>
   ```

2. **Create and activate a virtual environment:**

   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install all required dependencies:**
   This command installs both the API requirements and the core `vietvoicetts` library's dependencies.

   ```bash
   uv pip install -r requirements-api.txt
   pip install -e .
   ```

### 3. Running the API Locally

Start the development server using Uvicorn:

```bash
uv run run_api_server.py
uvicorn vietvoicetts.api:app --host 0.0.0.0 --port 8000 --reload
```

- `--reload`: Enables auto-reload, so the server will restart automatically when you change the code.

On the first run, the server will take a few moments to start as it downloads the TTS model file into the `models/` directory. Subsequent startups will be much faster.

Once running, the API will be available at `http://localhost:8000`.

---

## API Usage

You can interact with the running API using any HTTP client, such as `curl`.

### **Recommended: Direct Download (One-Step)**

This is the simplest way to get an audio file. It's ideal for scripts and automation.

**Endpoint:** `POST /api/v1/synthesize/download`

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/synthesize/download \
-H "Content-Type: application/json" \
-d '{
  "text": "Tệp này đã được tải xuống trực tiếp.",
  "gender": "female",
  "area": "southern"
}' \
-o direct_download.wav
```

This command will synthesize the text with a southern female voice and save the result directly to `direct_download.wav`.

### **For UIs: Asynchronous Generation (Two-Step)**

This pattern is best for web applications or long synthesis tasks, as it doesn't lock up the initial request.

**Step 1: Request the File Generation**

**Endpoint:** `POST /api/v1/synthesize/file`

```bash
curl -X POST http://localhost:8000/api/v1/synthesize/file \
-H "Content-Type: application/json" \
-d '{"text": "Đây là một quy trình hai bước."}'
```

The server will immediately respond with JSON containing a download URL:

```json
{
  "download_url": "/api/v1/download/a1b2c3d4e5",
  "duration_seconds": 1.78,
  "sample_rate": 24000,
  ...
}
```

**Step 2: Download the Generated File**

**Endpoint:** `GET /api/v1/download/{file_id}`

Use the `file_id` from the previous step to download the file.

```bash
# Replace 'a1b2c3d4e5' with the ID you received
curl http://localhost:8000/api/v1/download/a1b2c3d4e5 -o two_step_result.wav
```

### **For Web Playback: Inline Audio**

This endpoint is designed to be used in an HTML `<audio>` tag for immediate playback in a browser.

**Endpoint:** `POST /api/v1/synthesize`

### **Health Check**

Verify that the service is running and get its uptime.

**Endpoint:** `GET /api/v1/health`

```bash
curl http://localhost:8000/api/v1/health
```

---

## Configuration

Application settings can be configured using environment variables or a `.env` file in the project root.

**Example `.env` file:**

```
# You can override the default temporary directory path
# TMP_DIR_PATH="/path/to/your/custom/cache"
```

Refer to `vietvoicetts/api/settings.py` for all available configuration options.

## Path to Production

This API is a solid foundation. To make it fully production-grade, consider the following improvements:

- [ ] **Automated File Cleanup:** Implement background tasks to periodically delete old audio files from the temporary directory.
- [ ] **Persistent Caching:** Replace the in-memory file cache with a shared, persistent cache like Redis to support multiple server workers and survive restarts.
- [ ] **Containerization:** Package the application and its dependencies into a Docker image for consistent and scalable deployments.
- [ ] **Security Hardening:** Implement rate limiting, CORS policies, and other security best practices.
- [ ] **MP3 Support:** Add an optional `mp3` output format by integrating FFmpeg for on-the-fly audio conversion.
- [ ] **Observability:** Add structured logging, Prometheus metrics, and distributed tracing to monitor API performance and health.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
