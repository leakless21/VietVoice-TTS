# CLI Component Documentation

This document details the `vietvoicetts/cli.py` component, which provides the command-line interface for VietVoice TTS.

## 1. Overview

The CLI component allows users to interact with the VietVoice TTS system to synthesize speech from text. It supports both traditional command-line argument parsing and a new interactive menu-driven mode for easier configuration.

## 2. Key Classes and Functions

- **`main()`**: The primary entry point for the CLI. It checks for command-line arguments to determine whether to run in non-interactive or interactive mode.
- **`run_interactive_mode()`**: Orchestrates the interactive session, guiding the user through parameter collection, menu navigation, and synthesis confirmation.
- **`create_config(args: Union[argparse.Namespace, Dict[str, Any]]) -> ModelConfig`**: A helper function responsible for creating a `ModelConfig` object from either parsed command-line arguments (`argparse.Namespace`) or a dictionary of interactive settings.
- **`get_required_inputs() -> Dict[str, Any]`**: Prompts the user for the mandatory `text` and an output `filename` in interactive mode.
- **`get_default_settings() -> Dict[str, Any]`**: Returns a dictionary containing the default values for all optional parameters, used to initialize settings in interactive mode.
- **`display_main_menu(settings: Dict[str, Any])`**: Displays the main interactive menu, showing current parameter selections and available sections for editing.
- **`edit_voice_selection(settings: Dict[str, Any]) -> Dict[str, Any]`**: Allows users to modify voice-related parameters (`gender`, `group`, `area`, `emotion`).
- **`edit_reference_audio(settings: Dict[str, Any]) -> Dict[str, Any]`**: Manages input for reference audio and text with three modes:
  1. Select from bundled reference samples (with preview)
  2. Enter a custom path manually
  3. Clear existing reference audio
     Validates mutual requirement with reference text.
- **`edit_performance_tuning(settings: Dict[str, Any]) -> Dict[str, Any]`**: Handles parameters related to speech speed and random seed.
- **`edit_model_configuration(settings: Dict[str, Any]) -> Dict[str, Any]`**: Provides options for advanced model settings like `model_url`, `model_cache_dir`, `nfe_step`, and `fuse_nfe`.
- **`edit_audio_processing(settings: Dict[str, Any]) -> Dict[str, Any]`**: Allows adjustment of audio output characteristics such as `cross_fade_duration`, `max_chunk_duration`, and `min_target_duration`.
- **`edit_onnx_runtime(settings: Dict[str, Any]) -> Dict[str, Any]`**: Configures low-level ONNX Runtime settings, including thread counts and log severity.
- **`select_from_list(prompt: str, choices: list, current: Any) -> Optional[str]`**: A generic helper for selecting a value from a predefined list of choices, displaying current selection and allowing clearing.
- **`get_float_input(prompt: str, current: float, min_val: float, max_val: float) -> float`**: A helper for robustly collecting and validating float inputs within a specified range.
- **`get_int_input(prompt: str, current: int, min_val: int, max_val: int) -> int`**: A helper for robustly collecting and validating integer inputs within a specified range.
- **`get_optional_input(prompt: str, current: Optional[str]) -> Optional[str]`**: A helper for collecting optional string inputs, preserving the current value if no new input is provided.
- **`confirm_and_synthesize(settings: Dict[str, Any]) -> bool`**: Displays a summary of all selected settings, constructs the final output path as `output/filename.wav`, performs final validation, and initiates the speech synthesis process if confirmed by the user.

## 3. Interactive Flow

The interactive mode is activated when `vietvoicetts/cli.py` is run without any command-line arguments. The flow is as follows:

1.  **Welcome Message**: A colorful welcome message is displayed.
2.  **Required Inputs**: The user is first prompted to enter the `text` to synthesize and the `output` file path, as these are mandatory.
3.  **Main Menu Loop**:
    - The current settings are displayed, including a preview of the text and output path, and a summary of voice and reference audio settings if applicable.
    - A numbered menu presents various configuration sections (Voice Selection, Reference Audio, Performance Tuning, Model Configuration, Audio Processing, ONNX Runtime) and an option to "Confirm and Synthesize".
    - The user selects a section to edit or chooses to confirm.
4.  **Section Editing**:
    - Each section (e.g., "Voice Selection") has a dedicated function that prompts the user for relevant parameters.
    - Prompts show the current or default value and provide guidance (e.g., valid ranges, available choices).
    - Input validation is performed for each parameter (e.g., numeric type, range, enum choices). Invalid inputs prompt re-entry.
    - Users can clear optional selections by entering an empty value or '0' for list selections.
5.  **Confirmation and Synthesis**:
    - When "Confirm and Synthesize" is selected, a confirmation screen displays all chosen settings.
    - A final validation check is performed (e.g., ensuring `reference-audio` and `reference-text` are both present or absent).
    - The user is asked for final confirmation to proceed.
    - If confirmed, the settings are used to create a `ModelConfig` and initiate speech synthesis via `TTSApi`.
    - Success or error messages are displayed. If an error occurs, the user is returned to the main menu.

## 4. Design Considerations

- **User Experience**: Rich formatting using ANSI escape codes enhances readability and guides the user through the interactive process.
- **Modularity**: The interactive logic is separated into distinct functions for each menu section and input type, improving maintainability.
- **Validation Parity**: The interactive mode's validation rules are designed to be equivalent to the original `argparse` checks, ensuring consistent behavior.
- **Backward Compatibility**: Existing CLI integrations remain fully functional, as the interactive mode is only activated when no arguments are provided.
- **Default Sample Integration**: The interactive mode supports both bundled reference samples and custom paths for default references. When no explicit reference is provided, uses ModelConfig defaults that can be configured through CLI settings.
- **Python 3.8+ Compatibility**: The code adheres to Python 3.8+ syntax and features, including type hints.

## 5. File Location

The `cli.py` component is located at: [`vietvoicetts/cli.py`](vietvoicetts/cli.py)
