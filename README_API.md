# VietVoice TTS API Documentation

## Endpoints

| Path                      | Method | Description                | Parameters                                                                                                                                                |
| ------------------------- | ------ | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/api/v1/health`          | GET    | Service health check       | None                                                                                                                                                      |
| `/api/v1/synthesize`      | POST   | Stream audio bytes         | `text` (str, required), `speed` (float, optional), `output_format` (str, default "wav"), `gender` (enum), `group` (enum), `area` (enum), `emotion` (enum), `sample_iteration` (int, optional) |
| `/api/v1/synthesize/file` | POST   | Generate downloadable file | Same as /synthesize                                                                                                                                       |
| `/api/v1/download/{id}`   | GET    | Download generated file    | `id` (str)                                                                                                                                                |

### Synthesis Parameters

- **text** (`string`, required): Text to synthesize (max 500 characters).
- **speed** (`float`, optional): Speech speed (default: 0.9, range: 0.25–2.0).
- **output_format** (`string`, optional): Output audio format (default: `"wav"`).
- **gender** (`enum`, optional): `"male"` or `"female"`.
- **group** (`enum`, optional): `"story"`, `"news"`, `"audiobook"`, `"interview"`, `"review"`.
- **area** (`enum`, optional): `"northern"`, `"southern"`, `"central"`.
- **emotion** (`enum`, optional): `"neutral"`, `"serious"`, `"monotone"`, `"sad"`, `"surprised"`, `"happy"`, `"angry"`.
- **sample_iteration** (`integer`, optional): Choose which iteration of available samples to use (0-based index). When multiple voice samples match your filters, this allows you to select a specific one. If not specified, the first available sample is used.

## Example Request
```
uvicorn vietvoicetts.api:app --host 0.0.0.0 --port 8000 --reload
```
```bash
curl -X POST http://localhost:8000/api/v1/synthesize/file \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Xin chào thế giới",
    "speed": 1.0,
    "gender": "female",
    "group": "news",
    "area": "northern",
    "emotion": "happy",
    "sample_iteration": 0
  }'
```

## Response Formats

- `/synthesize`: Streams audio bytes (Content-Type: audio/wav)
- `/synthesize/file`: Returns JSON:
  ```json
  {
    "download_url": "/api/v1/download/abc123def4",
    "duration_seconds": 2.13,
    "sample_rate": 24000,
    "format": "wav",
    "file_size_bytes": 123456
  }
  ```
- `/download/{id}`: Returns audio file (Content-Type: audio/wav)

## Error Handling

- 400: Invalid request parameters (e.g., invalid enum value, sample_iteration out of range)
- 404: File not found
- 500: Internal server error

## Authentication

No authentication is required for any endpoint.

## Enum Reference

- **gender**: `"male"`, `"female"`
- **group**: `"story"`, `"news"`, `"audiobook"`, `"interview"`, `"review"`
- **area**: `"northern"`, `"southern"`, `"central"`
- **emotion**: `"neutral"`, `"serious"`, `"monotone"`, `"sad"`, `"surprised"`, `"happy"`, `"angry"`

## Sample Iteration Usage

The `sample_iteration` parameter allows you to choose which specific voice sample to use when multiple samples match your filter criteria. For example:

- If you specify `gender: "female"` and `emotion: "happy"`, there might be multiple female happy voice samples available
- Use `sample_iteration: 0` for the first sample, `sample_iteration: 1` for the second, and so on
- If you specify an index that's out of range, you'll get a 400 error with details about how many samples are available
- If you don't specify `sample_iteration`, the system defaults to using the first available sample (index 0)
