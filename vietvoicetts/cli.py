"""
Command-line interface for VietVoice TTS
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union

from .core import ModelConfig
from .core.model_config import MODEL_GENDER, MODEL_GROUP, MODEL_AREA, MODEL_EMOTION
from .client import TTSApi
from .reference_samples import (
    load_reference_samples,
    filter_samples as _filter_reference_samples,
    get_sample_path as _get_reference_sample_path,
    play_sample as _play_reference_sample,
    ReferenceSample,
)


# ANSI color codes for rich formatting
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VietVoice TTS - Vietnamese Text-to-Speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vietvoicetts "Hello world" output.wav
  vietvoicetts "Xin chào Việt Nam" output.wav --gender female --area northern
  vietvoicetts "Hello world" output.wav --reference-audio ref.wav --reference-text "Hello"

Interactive Mode:
  Run without arguments to enter interactive mode:
  vietvoicetts
        """
    )
    
    # Required arguments
    parser.add_argument("text", nargs='?', help="Text to synthesize")
    parser.add_argument("output", nargs='?', help="Output audio file path")
    
    # Voice selection
    parser.add_argument("--gender", choices=MODEL_GENDER, help="Voice gender")
    parser.add_argument("--group", choices=MODEL_GROUP, help="Voice group/style")
    parser.add_argument("--area", choices=MODEL_AREA, help="Voice area/accent")
    parser.add_argument("--emotion", choices=MODEL_EMOTION, help="Voice emotion")
    
    # Reference audio
    parser.add_argument("--reference-audio", help="Path to reference audio file")
    parser.add_argument("--reference-text", help="Text corresponding to reference audio")
    
    # Speed and random seed
    parser.add_argument("--speed", type=float, default=0.9, help="Speech speed multiplier")
    parser.add_argument("--random-seed", type=int, default=9527, help="Random seed. This is important for keeping the same voice when synthesizing.")

    # Model settings. These are not recommended to change.
    parser.add_argument("--model-url", help="URL to download model from")
    parser.add_argument("--model-cache-dir", help="Directory to cache model files")
    parser.add_argument("--nfe-step", type=int, default=32, help="Number of NFE steps")
    parser.add_argument("--fuse-nfe", type=int, default=1, help="Fuse NFE steps")
    
    # Audio processing
    parser.add_argument("--cross-fade-duration", type=float, default=0.1, 
                       help="Cross-fade duration in seconds")
    parser.add_argument("--max-chunk-duration", type=float, default=15.0,
                       help="Maximum chunk duration in seconds")
    parser.add_argument("--min-target-duration", type=float, default=1.0,
                       help="Minimum target duration in seconds")
    
    # ONNX Runtime settings
    parser.add_argument("--inter-op-threads", type=int, default=0,
                       help="Number of inter-op threads")
    parser.add_argument("--intra-op-threads", type=int, default=0,
                       help="Number of intra-op threads")
    parser.add_argument("--log-severity", type=int, default=4,
                       help="Log severity level")
    
    args = parser.parse_args()
    
    # Check if interactive mode should be activated
    if len(sys.argv) == 1:
        run_interactive_mode()
        return
    
    # Validate required arguments in non-interactive mode
    if not args.text or not args.output:
        parser.error("text and output arguments are required in non-interactive mode")
    
    # Validate reference audio/text
    if args.reference_audio and not args.reference_text:
        parser.error("--reference-text is required when using --reference-audio")
    if args.reference_text and not args.reference_audio:
        parser.error("--reference-audio is required when using --reference-text")
    
    try:
        # Create configuration
        config = create_config(args)
        
        # Create API instance
        api = TTSApi(config)
        
        # Synthesize speech
        duration = api.synthesize_to_file(
            text=args.text,
            output_path=args.output,
            gender=args.gender,
            group=args.group,
            area=args.area,
            emotion=args.emotion,
            reference_audio=args.reference_audio,
            reference_text=args.reference_text
        )
        
        print(f"✅ Synthesis complete! Duration: {duration:.2f}s")
        print(f"📄 Output saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def create_config(args: Union[argparse.Namespace, Dict[str, Any]]) -> ModelConfig:
    """Create ModelConfig from command line arguments or interactive settings"""
    if isinstance(args, dict):
        # Map interactive keys to ModelConfig fields and filter out None values
        config_params = {
            'model_url': args.get('model_url'),
            'nfe_step': args.get('nfe_step'),
            'fuse_nfe': args.get('fuse_nfe'),
            'speed': args.get('speed'),
            'random_seed': args.get('random_seed'),
            'cross_fade_duration': args.get('cross_fade_duration'),
            'max_chunk_duration': args.get('max_chunk_duration'),
            'min_target_duration': args.get('min_target_duration'),
            'inter_op_num_threads': args.get('inter_op_threads'),
            'intra_op_num_threads': args.get('intra_op_threads'),
            'log_severity_level': args.get('log_severity')
        }
        # Remove keys with None values so dataclass defaults are used
        final_params = {k: v for k, v in config_params.items() if v is not None}
        return ModelConfig(**final_params)
    else:
        # Handle argparse.Namespace (non-interactive mode)
        return ModelConfig(
            model_url=args.model_url or "https://huggingface.co/nguyenvulebinh/VietVoice-TTS/resolve/main/model-bin.pt",
            nfe_step=args.nfe_step,
            fuse_nfe=args.fuse_nfe,
            speed=args.speed,
            random_seed=args.random_seed,
            cross_fade_duration=args.cross_fade_duration,
            max_chunk_duration=args.max_chunk_duration,
            min_target_duration=args.min_target_duration,
            inter_op_num_threads=args.inter_op_threads,
            intra_op_num_threads=args.intra_op_threads,
            log_severity_level=args.log_severity
        )


def run_interactive_mode():
    """Run the interactive menu system"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎤 VietVoice TTS - Interactive Mode{Colors.RESET}")
    print(f"{Colors.GREEN}Welcome to the interactive text-to-speech synthesizer!{Colors.RESET}\n")
    
    # Collect required inputs first
    settings = get_required_inputs()
    
    # Set defaults for optional parameters
    settings.update(get_default_settings())
    
    # Main menu loop
    while True:
        display_main_menu(settings)
        choice = input(f"\n{Colors.YELLOW}Select option [1-7]: {Colors.RESET}").strip()
        
        if choice == '1':
            settings = edit_voice_selection(settings)
        elif choice == '2':
            settings = edit_reference_audio(settings)
        elif choice == '3':
            settings = edit_performance_tuning(settings)
        elif choice == '4':
            settings = edit_model_configuration(settings)
        elif choice == '5':
            settings = edit_audio_processing(settings)
        elif choice == '6':
            settings = edit_onnx_runtime(settings)
        elif choice == '7':
            if confirm_and_synthesize(settings):
                break
        else:
            print(f"{Colors.RED}❌ Invalid choice. Please select 1-7.{Colors.RESET}")


def get_required_inputs() -> Dict[str, Any]:
    """Get required text and output filename from user"""
    print(f"{Colors.CYAN}{Colors.BOLD}📋 Required Information{Colors.RESET}")
    
    text = input(f"{Colors.GREEN}Enter text to synthesize: {Colors.RESET}").strip()
    while not text:
        print(f"{Colors.RED}❌ Text cannot be empty.{Colors.RESET}")
        text = input(f"{Colors.GREEN}Enter text to synthesize: {Colors.RESET}").strip()
    
    default_output_folder = "output"
    default_filename = "output"
    output = input(f"{Colors.GREEN}Enter output filename (default: {default_filename}.wav, folder: {default_output_folder}/): {Colors.RESET}").strip()
    if not output:
        output = default_filename
    
    return {'text': text, 'output': output}


def get_default_settings() -> Dict[str, Any]:
    """Get default settings for optional parameters"""
    return {
        'gender': "female",
        'group': None,
        'area': "northern",
        'emotion': "neutral",
        'reference_audio': None,
        'reference_text': None,
        'speed': 0.9,
        'random_seed': 9527,
        'model_url': None,
        'nfe_step': 32,
        'fuse_nfe': 1,
        'cross_fade_duration': 0.1,
        'max_chunk_duration': 15.0,
        'min_target_duration': 1.0,
        'inter_op_threads': 0,
        'intra_op_threads': 0,
        'log_severity': 4
    }


def display_main_menu(settings: Dict[str, Any]):
    """Display the main interactive menu"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎯 Main Menu{Colors.RESET}")
    print(f"{Colors.BLUE}Current Settings:{Colors.RESET}")
    
    # Display current settings
    text_preview = settings['text'][:50] + '...' if len(settings['text']) > 50 else settings['text']
    print(f"  Text: {Colors.GREEN}{text_preview}{Colors.RESET}")
    print(f"  Output: {Colors.GREEN}{settings['output']}{Colors.RESET}")
    
    voice_info = []
    if settings['gender']:
        voice_info.append(f"Gender: {settings['gender']}")
    if settings['group']:
        voice_info.append(f"Group: {settings['group']}")
    if settings['area']:
        voice_info.append(f"Area: {settings['area']}")
    if settings['emotion']:
        voice_info.append(f"Emotion: {settings['emotion']}")
    
    if voice_info:
        print(f"  Voice: {Colors.YELLOW}{', '.join(voice_info)}{Colors.RESET}")
    
    if settings['reference_audio'] and settings['reference_text']:
        print(f"  Reference: {Colors.MAGENTA}Enabled{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}Options:{Colors.RESET}")
    print("  1. Voice Selection")
    print("  2. Reference Audio")
    print("  3. Performance Tuning")
    print("  4. Model Configuration")
    print("  5. Audio Processing")
    print("  6. ONNX Runtime")
    print("  7. Confirm and Synthesize")


def edit_voice_selection(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit voice selection parameters"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎭 Voice Selection{Colors.RESET}")
    
    settings['gender'] = select_from_list("Gender", MODEL_GENDER, settings['gender'])
    settings['group'] = select_from_list("Group", MODEL_GROUP, settings['group'])
    settings['area'] = select_from_list("Area", MODEL_AREA, settings['area'])
    settings['emotion'] = select_from_list("Emotion", MODEL_EMOTION, settings['emotion'])
    
    return settings


def edit_reference_audio(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit reference audio parameters.

    Offers three modes:
    1. Select from bundled reference samples (with preview).
    2. Enter a custom path manually.
    3. Clear existing reference audio.
    """

    print(f"\n{Colors.CYAN}{Colors.BOLD}🎵 Reference Audio{Colors.RESET}")

    print("Options:")
    print("  1. Choose from built-in samples")
    print("  2. Enter custom path")
    print("  0. Clear reference audio")

    choice = input(f"{Colors.YELLOW}Select option [0-2]: {Colors.RESET}").strip()

    if choice == "1":
        selected = _browse_reference_samples()
        if selected:
            settings["reference_audio"] = str(_get_reference_sample_path(selected))
            settings["reference_text"] = selected.text
    elif choice == "2":
        ref_audio = input(
            f"{Colors.GREEN}Reference audio path (current: {settings.get('reference_audio') or 'None'}): {Colors.RESET}"
        ).strip()
        if ref_audio:
            settings["reference_audio"] = ref_audio
            # Ask for corresponding text
            ref_text = input(
                f"{Colors.GREEN}Reference text (current: {settings.get('reference_text') or 'None'}): {Colors.RESET}"
            ).strip()
            if ref_text:
                settings["reference_text"] = ref_text
        else:
            print(f"{Colors.RED}❌ Path cannot be empty.{Colors.RESET}")
    elif choice == "0":
        settings["reference_audio"] = None
        settings["reference_text"] = None

    return settings


def edit_performance_tuning(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit performance tuning parameters"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}⚡ Performance Tuning{Colors.RESET}")
    
    settings['speed'] = get_float_input("Speech speed multiplier", settings['speed'], 0.1, 3.0)
    settings['random_seed'] = get_int_input("Random seed", settings['random_seed'], 0, 999999)
    
    return settings


def edit_model_configuration(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit model configuration parameters"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔧 Model Configuration{Colors.RESET}")
    
    settings['model_url'] = get_optional_input("Model URL", settings['model_url'])
    settings['nfe_step'] = get_int_input("NFE steps", settings['nfe_step'], 1, 100)
    settings['fuse_nfe'] = get_int_input("Fuse NFE steps", settings['fuse_nfe'], 0, 10)
    
    return settings


def edit_audio_processing(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit audio processing parameters"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎚️ Audio Processing{Colors.RESET}")
    
    settings['cross_fade_duration'] = get_float_input("Cross-fade duration (seconds)", settings['cross_fade_duration'], 0.01, 5.0)
    settings['max_chunk_duration'] = get_float_input("Max chunk duration (seconds)", settings['max_chunk_duration'], 1.0, 60.0)
    settings['min_target_duration'] = get_float_input("Min target duration (seconds)", settings['min_target_duration'], 0.1, 10.0)
    
    return settings


def edit_onnx_runtime(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Edit ONNX Runtime parameters"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔩 ONNX Runtime{Colors.RESET}")
    
    settings['inter_op_threads'] = get_int_input("Inter-op threads", settings['inter_op_threads'], 0, 64)
    settings['intra_op_threads'] = get_int_input("Intra-op threads", settings['intra_op_threads'], 0, 64)
    settings['log_severity'] = get_int_input("Log severity level", settings['log_severity'], 0, 5)
    
    return settings


def select_from_list(prompt: str, choices: list, current: Any) -> Optional[str]:
    """Let user select from a list of choices"""
    print(f"\n{Colors.YELLOW}{prompt}:{Colors.RESET}")
    for i, choice in enumerate(choices, 1):
        marker = f"{Colors.GREEN}✓{Colors.RESET}" if choice == current else " "
        print(f"  {i}. {marker} {choice}")
    print(f"  0. {Colors.RED}Clear selection{Colors.RESET}")
    
    while True:
        try:
            choice_num = int(input(f"Select option [0-{len(choices)}] (current: {current or 'None'}): ").strip())
            if choice_num == 0:
                return None
            elif 1 <= choice_num <= len(choices):
                return choices[choice_num - 1]
            else:
                print(f"{Colors.RED}❌ Invalid choice. Please select 0-{len(choices)}.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid number.{Colors.RESET}")


# ---------------------------------------------------------------------------
# Built-in reference sample browser helpers
# ---------------------------------------------------------------------------


def _browse_reference_samples() -> Optional[ReferenceSample]:
    """Interactive browser for bundled reference audio samples.

    Returns the chosen ``ReferenceSample`` or ``None`` if the user cancels.
    """

    all_samples = load_reference_samples()
    if not all_samples:
        print(f"{Colors.RED}❌ No built-in reference samples found.{Colors.RESET}")
        return None

    # Active filters
    filters = {"gender": None, "group": None, "area": None, "emotion": None}

    while True:
        # Apply filters
        filtered = _filter_reference_samples(all_samples, **filters)

        print(f"\n{Colors.CYAN}{Colors.BOLD}🎧 Reference Sample Browser{Colors.RESET}")
        print("Filters:")
        for k, v in filters.items():
            print(f"  {k.capitalize():8}: {v if v else 'Any'}")

        if not filtered:
            print(f"{Colors.RED}No samples match current filters.{Colors.RESET}")
        else:
            print("\nMatching Samples (enter number to select, 'p<num>' to play):")
            for idx, s in enumerate(filtered[:50], 1):
                meta = f"{s.gender}/{s.group}/{s.area}/{s.emotion}"
                preview = (s.text[:60] + "…") if len(s.text) > 60 else s.text
                print(f"  {idx:2}. {s.filename:<40} | {meta:<40} | {preview}")
            if len(filtered) > 50:
                print(f"  … (+{len(filtered)-50} more) use filters to narrow list …")

        print("\nOptions:")
        print("  g – set gender filter     | a – set area filter")
        print("  r – set group filter      | e – set emotion filter")
        print("  c – clear all filters     | 0 – cancel and go back")

        choice = input(f"{Colors.YELLOW}Enter choice: {Colors.RESET}").strip().lower()

        # Cancel / back
        if choice == "0":
            return None

        # Filter setters
        if choice == "g":
            filters["gender"] = select_from_list("Gender", [*MODEL_GENDER, "Any"], filters["gender"])
            if filters["gender"] == "Any":
                filters["gender"] = None
            continue
        if choice == "r":
            filters["group"] = select_from_list("Group", [*MODEL_GROUP, "Any"], filters["group"])
            if filters["group"] == "Any":
                filters["group"] = None
            continue
        if choice == "a":
            filters["area"] = select_from_list("Area", [*MODEL_AREA, "Any"], filters["area"])
            if filters["area"] == "Any":
                filters["area"] = None
            continue
        if choice == "e":
            filters["emotion"] = select_from_list("Emotion", [*MODEL_EMOTION, "Any"], filters["emotion"])
            if filters["emotion"] == "Any":
                filters["emotion"] = None
            continue

        # Playback request e.g. "p3"
        if choice.startswith("p") and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(filtered):
                _play_reference_sample(filtered[idx])
            else:
                print(f"{Colors.RED}Invalid sample index.{Colors.RESET}")
            continue

        # Selection by index
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(filtered):
                return filtered[idx]
            print(f"{Colors.RED}Invalid sample index.{Colors.RESET}")

        # Unknown input → loop again


def get_float_input(prompt: str, current: float, min_val: float, max_val: float) -> float:
    """Get validated float input from user"""
    while True:
        try:
            value_str = input(f"{Colors.GREEN}{prompt} [{min_val}-{max_val}] (current: {current}): {Colors.RESET}").strip()
            if not value_str:
                return current
            value = float(value_str)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"{Colors.RED}❌ Value must be between {min_val} and {max_val}.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid number.{Colors.RESET}")


def get_int_input(prompt: str, current: int, min_val: int, max_val: int) -> int:
    """Get validated integer input from user"""
    while True:
        try:
            value_str = input(f"{Colors.GREEN}{prompt} [{min_val}-{max_val}] (current: {current}): {Colors.RESET}").strip()
            if not value_str:
                return current
            value = int(value_str)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"{Colors.RED}❌ Value must be between {min_val} and {max_val}.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid integer.{Colors.RESET}")


def get_optional_input(prompt: str, current: Optional[str]) -> Optional[str]:
    """Get optional string input from user"""
    value = input(f"{Colors.GREEN}{prompt} (current: {current or 'None'}): {Colors.RESET}").strip()
    if not value:
        return current
    return value if value else None


def confirm_and_synthesize(settings: Dict[str, Any]) -> bool:
    """Display confirmation screen and synthesize if confirmed"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}✅ Confirmation Screen{Colors.RESET}")
    
    # Construct final output path
    output_dir = Path("output")
    output_filename = settings['output']
    if not output_filename.lower().endswith('.wav'):
        output_filename += '.wav'
    final_output_path = output_dir / output_filename

    # Validate reference audio/text mutual requirement
    if bool(settings.get('reference_audio')) != bool(settings.get('reference_text')):
        print(f"{Colors.RED}❌ Error: Reference audio and text must both be provided or both be empty.{Colors.RESET}")
        input("Press Enter to return to menu...")
        return False
    
    # Display all settings
    print(f"\n{Colors.BLUE}Final Settings:{Colors.RESET}")
    print(f"  Text: {Colors.GREEN}{settings['text']}{Colors.RESET}")
    print(f"  Output Path: {Colors.GREEN}{final_output_path}{Colors.RESET}")
    
    if settings.get('gender'):
        print(f"  Gender: {Colors.YELLOW}{settings['gender']}{Colors.RESET}")
    if settings.get('group'):
        print(f"  Group: {Colors.YELLOW}{settings['group']}{Colors.RESET}")
    if settings.get('area'):
        print(f"  Area: {Colors.YELLOW}{settings['area']}{Colors.RESET}")
    if settings.get('emotion'):
        print(f"  Emotion: {Colors.YELLOW}{settings['emotion']}{Colors.RESET}")
    
    if settings.get('reference_audio') and settings.get('reference_text'):
        print(f"  Reference Audio: {Colors.MAGENTA}{settings['reference_audio']}{Colors.RESET}")
        print(f"  Reference Text: {Colors.MAGENTA}{settings['reference_text']}{Colors.RESET}")
    
    print(f"  Speed: {Colors.CYAN}{settings['speed']:.2f}{Colors.RESET}")
    print(f"  Random Seed: {Colors.CYAN}{settings['random_seed']}{Colors.RESET}")
    
    print(f"{Colors.BOLD}\nModel Parameters:{Colors.RESET}")
    print(f"  Model URL: {Colors.CYAN}{settings.get('model_url') or 'Default'}{Colors.RESET}")
    print(f"  NFE Step: {Colors.CYAN}{settings.get('nfe_step', 32)}{Colors.RESET}")
    print(f"  Fuse NFE: {Colors.CYAN}{settings.get('fuse_nfe', 1)}{Colors.RESET}")
    
    print(f"  Cross-fade Duration: {Colors.CYAN}{settings.get('cross_fade_duration', 0.1)}{Colors.RESET}")
    print(f"  Max Chunk Duration: {Colors.CYAN}{settings.get('max_chunk_duration', 15.0)}{Colors.RESET}")
    print(f"  Min Target Duration: {Colors.CYAN}{settings.get('min_target_duration', 1.0)}{Colors.RESET}")
    
    print(f"  Inter-op Threads: {Colors.CYAN}{settings.get('inter_op_threads', 0)}{Colors.RESET}")
    print(f"  Intra-op Threads: {Colors.CYAN}{settings.get('intra_op_threads', 0)}{Colors.RESET}")
    print(f"  Log Severity: {Colors.CYAN}{settings.get('log_severity', 4)}{Colors.RESET}")
    
    confirm = input(f"\n{Colors.YELLOW}Proceed with synthesis? (yes/no): {Colors.RESET}").strip().lower()
    if confirm == 'yes':
        try:
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            config = create_config(settings) # Pass dictionary directly
            api = TTSApi(config)
            
            duration = api.synthesize_to_file(
                text=settings['text'],
                output_path=str(final_output_path),
                gender=settings.get('gender'),
                group=settings.get('group'),
                area=settings.get('area'),
                emotion=settings.get('emotion'),
                reference_audio=settings.get('reference_audio'),
                reference_text=settings.get('reference_text')
            )
            
            print(f"\n✅ Synthesis complete! Duration: {duration:.2f}s")
            print(f"📄 Output saved to: {final_output_path}")
            return True
        except Exception as e:
            print(f"❌ Error during synthesis: {e}", file=sys.stderr)
            input("Press Enter to return to menu...")
            return False
    else:
        print(f"{Colors.YELLOW}Synthesis cancelled.{Colors.RESET}")
        return False


if __name__ == "__main__":
    main()