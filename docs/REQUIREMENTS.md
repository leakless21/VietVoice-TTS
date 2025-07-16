# VietVoice TTS CLI - Interactive Menu Requirements

## 1. Functional Requirements

- **FR-1: Preserve Non-Interactive Mode:** The CLI MUST retain its current functionality. When arguments are provided via the command line, the script should execute non-interactively as it does currently.
- **FR-2: Interactive Mode Trigger:** The script MUST enter an interactive menu mode if no command-line arguments are provided.
- **FR-3: Parameter Grouping:** The interactive menu MUST group parameters into logical sections to guide the user.
- **FR-4: Input Validation:** The interactive menu MUST validate user input to the same extent as the existing `argparse` implementation. This includes:
  - **FR-4.1:** Mutual requirement for reference audio and reference text.
  - **FR-4.2:** Constrained choices for enumeration-type parameters (e.g., gender, area).
  - **FR-4.3:** Validation for numeric types.
- **FR-5: Default Values:** The interactive menu MUST provide default values for parameters, matching the defaults in the current `argparse` setup.
- **FR-6: Confirmation Screen:** Before executing the synthesis, the interactive menu MUST display a confirmation screen showing all the user's selections.
- **FR-7: Execution:** After confirmation, the script MUST proceed with the TTS synthesis using the selected parameters.
- **FR-8: Simple UI:** The interactive menu should be implemented using Python's built-in `input()` function with clear formatting for simplicity.

## 2. Non-Functional Requirements

- **NFR-1: Backward Compatibility:** The introduction of the interactive menu MUST NOT break existing scripts or workflows that use the CLI non-interactively.
- **NFR-2: Usability:** The interactive menu should be intuitive and easy to navigate for users unfamiliar with the command-line arguments.
- **NFR-3: Maintainability:** The code for the interactive menu should be well-structured and separated from the core TTS logic to ensure maintainability.
