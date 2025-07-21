# Project Requirements

## 1. Functional Requirements

- **FR-1: Preserve Non-Interactive Mode:** The CLI MUST retain its current functionality. When arguments are provided via the command line, the script should execute non-interactively as it does currently.
- **FR-2: Interactive Mode Trigger:** The script MUST enter an interactive menu mode if no command-line arguments are provided.
- **FR-3: Parameter Grouping:** The interactive menu MUST group parameters into logical sections to guide the user.
- **FR-4: Input Validation:** The interactive menu MUST validate user input to the same extent as the existing `argparse` implementation. This includes:

  - **FR-4.1:** Mutual requirement for reference audio and reference text.
  - **FR-4.2:** Constrained choices for enumeration-type parameters (e.g., gender, area).
  - **FR-4.3:** Validation for numeric types.

- **FR-4.4:** API enum parameters for synthesis must use the following allowed values:
  - `gender`: "male", "female"
  - `group`: "story", "news", "audiobook", "interview", "review"
  - `area`: "northern", "southern", "central"
  - `emotion`: "neutral", "serious", "monotone", "sad", "surprised", "happy", "angry"
  - These must be validated and documented in the API schema.
- **FR-5: Default Values:** The interactive menu MUST provide default values for parameters, matching the defaults in the current `argparse` setup.
- **FR-6: Confirmation Screen:** Before executing the synthesis, the interactive menu MUST display a confirmation screen showing all the user's selections.

## 2. New Functional Requirements

- **FR-7: Configurable Default Output Folder:** The default output folder for generated audio files MUST be configurable. The initial default value will be "output".
- **FR-8: Configurable Default Voice:** The default voice gender MUST be configurable. The initial default value will be "female".
- **FR-9: Configurable Default Emotion:** The default voice emotion MUST be configurable. The initial default value will be "neutral".
- **FR-10: Client API Defaults:** The high-level client API (`vietvoicetts/client.py`) MUST use "female" as the default gender and "neutral" as the default emotion if not explicitly provided.

### API Endpoints

- **FR-11: Health Check Endpoint:** The API MUST provide a `GET /api/v1/health` endpoint to report service health and uptime.
- **FR-12: Streaming Synthesis Endpoint:** The API MUST provide a `POST /api/v1/synthesize` endpoint to stream audio bytes directly to the caller.
- **FR-13: File Synthesis Endpoint:** The API MUST provide a `POST /api/v1/synthesize/file` endpoint to generate an audio file and return a download link.
- **FR-14: Download Endpoint:** The API MUST provide a `GET /api/v1/download/{file_id}` endpoint to download previously generated audio files.

### Error Handling Requirements

- **ER-1:** The API MUST return a clear error response if a requested file is not found or has expired.
- **ER-2:** The API MUST validate all input parameters and return descriptive errors for invalid requests (e.g., missing required fields, unsupported values).
- **ER-3:** The API MUST handle internal errors gracefully and return a generic error message without exposing sensitive details.

### Audio Format Constraints

- **AF-1:** The API MUST support output in WAV format only (`output_format: "wav"`).
- **AF-2:** All audio files MUST be single-channel (mono) and use the configured sample rate.
- **AF-3:** The API MUST set appropriate `Content-Type` and `Content-Disposition` headers for audio responses.
