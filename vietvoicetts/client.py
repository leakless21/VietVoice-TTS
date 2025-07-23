"""
High-level API for VietVoice TTS
"""

import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple, Union, Literal
import numpy as np

from .core import ModelConfig, TTSEngine
from .core.model_config import MODEL_GENDER, MODEL_GROUP, MODEL_AREA, MODEL_EMOTION


class TTSApi:
    """High-level API for VietVoice TTS"""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        """Initialize TTS API
        
        Args:
            config: ModelConfig instance (optional, uses default if not provided)
        """
        self.config = config or ModelConfig()
        self._engine = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._engine:
            self._engine.cleanup()
    
    @property
    def engine(self) -> TTSEngine:
        """Get the TTS engine, creating it if needed"""
        if self._engine is None:
            self._engine = TTSEngine(self.config)
        return self._engine
    
    def synthesize(self, text: str,
                   gender: Optional[str] = None,
                   group: Optional[str] = None,
                   area: Optional[str] = None,
                   emotion: Optional[str] = None,
                   sample_iteration: Optional[int] = None,
                   output_path: Optional[str] = None,
                   reference_audio: Optional[str] = None,
                   reference_text: Optional[str] = None) -> Tuple[np.ndarray, float]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            gender: Voice gender filter
            group: Voice group filter
            area: Voice area filter
            emotion: Voice emotion filter
            sample_iteration: Which iteration of available samples to use (0-based)
            output_path: Path to save the generated audio (optional)
            reference_audio: Path to reference audio file (optional)
            reference_text: Reference text matching the reference audio (optional)
            
        Returns:
            Tuple of (generated_audio_array, generation_time_seconds)
        """
        if text is None:
            raise ValueError("Text cannot be None")
        return self.engine.synthesize(
            text=text,
            gender=gender,
            group=group,
            area=area,
            emotion=emotion,
            sample_iteration=sample_iteration,
            output_path=output_path,
            reference_audio=reference_audio,
            reference_text=reference_text
        )
    
    def synthesize_to_file(self, text: str, output_path: str,
                           gender: Optional[str] = None,
                           group: Optional[str] = None,
                           area: Optional[str] = None,
                           emotion: Optional[str] = None,
                           sample_iteration: Optional[int] = None,
                           reference_audio: Optional[str] = None,
                           reference_text: Optional[str] = None) -> float:
        """
        Synthesize speech and save to file
        
        Args:
            text: Text to synthesize
            output_path: Path to save the generated audio
            gender: Voice gender filter
            group: Voice group filter
            area: Voice area filter
            emotion: Voice emotion filter
            sample_iteration: Which iteration of available samples to use (0-based)
            reference_audio: Path to reference audio file (optional)
            reference_text: Reference text matching the reference audio (optional)
            
        Returns:
            Generation time in seconds
        """
        result = self.synthesize(
            text=text,
            output_path=output_path,
            gender=gender,
            group=group,
            area=area,
            emotion=emotion,
            sample_iteration=sample_iteration,
            reference_audio=reference_audio,
            reference_text=reference_text
        )
        if result is None:
            return 0.0
        _, generation_time = result
        return generation_time
    
    def synthesize_to_bytes(self, text: str,
                           gender: Optional[str] = None,
                           group: Optional[str] = None,
                           area: Optional[str] = None,
                           emotion: Optional[str] = None,
                           sample_iteration: Optional[int] = None,
                           reference_audio: Optional[str] = None,
                           reference_text: Optional[str] = None) -> Tuple[bytes, float]:
        """
        Synthesize speech and return as bytes
        
        Args:
            text: Text to synthesize
            gender: Voice gender filter
            group: Voice group filter
            area: Voice area filter
            emotion: Voice emotion filter
            sample_iteration: Which iteration of available samples to use (0-based)
            reference_audio: Path to reference audio file (optional)
            reference_text: Reference text matching the reference audio (optional)
            
        Returns:
            Tuple of (wav_bytes, generation_time_seconds)
        """
        # Local import to avoid circular dependency with `vietvoicetts.api.tts_engine`
        from vietvoicetts.api.settings import settings as api_settings  # pylint: disable=import-outside-toplevel

        with tempfile.NamedTemporaryFile(
                suffix='.wav', delete=False, dir=api_settings.TMP_DIR_PATH) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            generation_time = self.synthesize_to_file(
                text=text,
                output_path=tmp_path,
                gender=gender,
                group=group,
                area=area,
                emotion=emotion,
                sample_iteration=sample_iteration,
                reference_audio=reference_audio,
                reference_text=reference_text
            )
            
            with open(tmp_path, 'rb') as f:
                wav_bytes = f.read()
            
            return wav_bytes, generation_time
            
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def validate_configuration(self, reference_audio: Optional[str] = None) -> bool:
        """
        Validate configuration
        
        Args:
            reference_audio: Path to reference audio file to validate against (optional)
            
        Returns:
            True if configuration is valid
        """
        return self.engine.validate_configuration(reference_audio)
    
    def cleanup(self):
        """Clean up resources"""
        if self._engine:
            self._engine.cleanup()
            self._engine = None


# Convenience functions for simple usage
def synthesize(text: str,
               output_path: str,
               gender: Optional[str] = None,
               group: Optional[str] = None,
               area: Optional[str] = None,
               emotion: Optional[str] = None,
               sample_iteration: Optional[int] = None,
               reference_audio: Optional[str] = None,
               reference_text: Optional[str] = None,
               config: Optional[ModelConfig] = None) -> float:
    """
    Convenience function to synthesize speech and save to file
    
    Args:
        text: Text to synthesize
        output_path: Path to save the output WAV file
        gender: Voice gender (male/female) - optional
        group: Voice group - optional
        area: Voice area - optional
        emotion: Voice emotion - optional
        sample_iteration: Which iteration of available samples to use (0-based) - optional
        reference_audio: Path to reference audio file - optional
        reference_text: Reference text matching the audio - optional
        config: ModelConfig instance (optional)
    
    Returns:
        Duration of synthesized audio in seconds
    """
    api = TTSApi(config)
    return api.synthesize_to_file(
        text=text,
        output_path=output_path,
        gender=gender,
        group=group,
        area=area,
        emotion=emotion,
        sample_iteration=sample_iteration,
        reference_audio=reference_audio,
        reference_text=reference_text
    )


def synthesize_to_bytes(text: str,
                        gender: Optional[str] = None,
                        group: Optional[str] = None,
                        area: Optional[str] = None,
                        emotion: Optional[str] = None,
                        sample_iteration: Optional[int] = None,
                        reference_audio: Optional[str] = None,
                        reference_text: Optional[str] = None,
                        config: Optional[ModelConfig] = None) -> Tuple[bytes, float]:
    """
    Convenience function to synthesize speech and return as bytes
    
    Args:
        text: Text to synthesize
        gender: Voice gender (male/female) - optional
        group: Voice group - optional
        area: Voice area - optional
        emotion: Voice emotion - optional
        sample_iteration: Which iteration of available samples to use (0-based) - optional
        reference_audio: Path to reference audio file - optional
        reference_text: Reference text matching the audio - optional
        config: ModelConfig instance (optional)
    
    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """
    api = TTSApi(config)
    return api.synthesize_to_bytes(
        text=text,
        gender=gender,
        group=group,
        area=area,
        emotion=emotion,
        sample_iteration=sample_iteration,
        reference_audio=reference_audio,
        reference_text=reference_text
    ) 