"""
TTS Engine - Main speech synthesis engine
"""

import time
import numpy as np
import torch
from typing import List, Tuple, Optional, Generator
from tqdm import tqdm

from .model_config import ModelConfig
from .model import ModelSessionManager
from .text_processor import TextProcessor
from .audio_processor import AudioProcessor


class TTSEngine:
    """Main TTS engine for inference"""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model_session_manager = ModelSessionManager(self.config)
        self.model_session_manager.load_models()
        
        if not self.model_session_manager.vocab_path:
            raise RuntimeError("Vocabulary file not found in model tar archive")
        
        self.text_processor = TextProcessor(self.model_session_manager.vocab_path)
        self.audio_processor = AudioProcessor()
        self.sample_cache = {}
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.model_session_manager:
            self.model_session_manager.cleanup()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def _prepare_inputs(self, reference_audio_path_or_bytes: str, reference_text: str, 
                       target_text: str) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """Prepare all inputs for inference, handling text chunking if needed"""
        audio = self.audio_processor.load_audio(reference_audio_path_or_bytes, self.config.sample_rate)
        audio = audio.reshape(1, 1, -1)

        # Clean text
        reference_text = self.text_processor.clean_text(reference_text)
        target_text = self.text_processor.clean_text(target_text)
        
        # Calculate reference audio duration and text length
        ref_text_len = self.text_processor.calculate_text_length(reference_text, self.config.pause_punctuation)
        ref_audio_len = audio.shape[-1] // self.config.hop_length + 1
        ref_audio_duration = audio.shape[-1] / self.config.sample_rate
        
        # Estimate speaking rate (characters per second)
        speaking_rate = ref_text_len / ref_audio_duration if ref_audio_duration > 0 else 100
        
        # Calculate total duration including reference audio
        target_text_len = self.text_processor.calculate_text_length(target_text, self.config.pause_punctuation)
        target_audio_duration = max(target_text_len / speaking_rate / self.config.speed, self.config.min_target_duration)
        total_estimated_duration = ref_audio_duration + target_audio_duration
        
        # Determine if chunking is needed
        if total_estimated_duration <= self.config.max_chunk_duration:
            # Single chunk processing
            chunks = [target_text]
            print(f"Single chunk: total estimated duration {total_estimated_duration:.1f}s (ref: {ref_audio_duration:.1f}s + target: {target_audio_duration:.1f}s)")
        else:
            # Multiple chunks needed
            # Calculate available duration for target text per chunk (excluding reference audio)
            # Add a small safety margin to ensure chunks don't exceed the limit
            safety_margin = 1.0  # seconds
            available_target_duration = self.config.max_chunk_duration - ref_audio_duration - safety_margin
            if available_target_duration <= 0:
                raise ValueError(f"Reference audio duration ({ref_audio_duration:.1f}s) exceeds max chunk duration ({self.config.max_chunk_duration}s)")
            
            # Calculate max characters per chunk based on available duration
            max_chars_per_chunk = int(speaking_rate * available_target_duration * self.config.speed)
            chunks = self.text_processor.chunk_text(target_text, max_chars=max_chars_per_chunk)
            
            # Post-process: verify each chunk meets duration requirements
            final_chunks = []
            for chunk in chunks:
                chunk_text_len = self.text_processor.calculate_text_length(chunk, self.config.pause_punctuation)
                chunk_target_duration = max(chunk_text_len / speaking_rate / self.config.speed, self.config.min_target_duration)
                chunk_total_duration = ref_audio_duration + chunk_target_duration
                
                if chunk_total_duration <= self.config.max_chunk_duration:
                    final_chunks.append(chunk)
                else:
                    # Split this chunk further
                    print(f"Warning: Chunk too long ({chunk_total_duration:.1f}s), splitting further...")
                    # Calculate a smaller max_chars for this specific chunk
                    smaller_max_chars = int(len(chunk) * available_target_duration / chunk_target_duration * 0.9)  # 90% safety
                    sub_chunks = self.text_processor.chunk_text(chunk, max_chars=smaller_max_chars)
                    final_chunks.extend(sub_chunks)
            
            chunks = final_chunks
            print(f"Long text detected (total estimated {total_estimated_duration:.1f}s), split into {len(chunks)} chunks")
            print(f"Reference audio: {ref_audio_duration:.1f}s, available per chunk: {available_target_duration:.1f}s (with {safety_margin}s safety margin)")
        
        # Prepare inputs for each chunk
        inputs_list = []
        for i, chunk in enumerate(chunks):
            chunk_text_len = self.text_processor.calculate_text_length(chunk, self.config.pause_punctuation)
            
            # Calculate target duration with minimum enforcement
            chunk_target_duration = max(chunk_text_len / speaking_rate / self.config.speed, self.config.min_target_duration)
            
            # Calculate chunk_audio_len based on the enforced target duration
            # Convert target duration to audio length units
            target_audio_samples = int(chunk_target_duration * self.config.sample_rate)
            target_audio_len = target_audio_samples // self.config.hop_length + 1
            chunk_audio_len = ref_audio_len + target_audio_len
            
            max_duration = np.array([chunk_audio_len], dtype=np.int64)
            
            combined_text = [list(reference_text + chunk)]
            text_ids = self.text_processor.text_to_indices(combined_text)
            time_step = np.array([0], dtype=np.int32)
            
            inputs_list.append((audio, text_ids, max_duration, time_step))
            
            # Calculate and display total duration for this chunk
            chunk_total_duration = ref_audio_duration + chunk_target_duration
            print(f"Chunk {i+1}/{len(chunks)}: {len(chunk)} chars, total duration {chunk_total_duration:.1f}s (ref: {ref_audio_duration:.1f}s + target: {chunk_target_duration:.1f}s). Content: {chunk}")
        
        return inputs_list
    
    def _run_preprocess(self, audio: np.ndarray, text_ids: np.ndarray, 
                       max_duration: np.ndarray) -> Tuple[np.ndarray, ...]:
        """Run preprocessing model"""
        session = self.model_session_manager.sessions['preprocess']
        input_names = self.model_session_manager.input_names['preprocess']
        output_names = self.model_session_manager.output_names['preprocess']
        
        inputs = {
            input_names[0]: audio,
            input_names[1]: text_ids,
            input_names[2]: max_duration
        }
        
        return session.run(output_names, inputs)
    
    def _run_transformer_steps(self, noise: np.ndarray, rope_cos_q: np.ndarray,
                              rope_sin_q: np.ndarray, rope_cos_k: np.ndarray,
                              rope_sin_k: np.ndarray, cat_mel_text: np.ndarray,
                              cat_mel_text_drop: np.ndarray, time_step: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Run transformer model iteratively"""
        session = self.model_session_manager.sessions['transformer']
        input_names = self.model_session_manager.input_names['transformer']
        output_names = self.model_session_manager.output_names['transformer']
        
        for i in tqdm(range(0, self.config.nfe_step - 1, self.config.fuse_nfe), 
                      desc="Processing", 
                      total=self.config.nfe_step // self.config.fuse_nfe - 1):
            
            inputs = {
                input_names[0]: noise,
                input_names[1]: rope_cos_q,
                input_names[2]: rope_sin_q,
                input_names[3]: rope_cos_k,
                input_names[4]: rope_sin_k,
                input_names[5]: cat_mel_text,
                input_names[6]: cat_mel_text_drop,
                input_names[7]: time_step
            }
            
            noise, time_step = session.run(output_names, inputs)
        
        return noise, time_step
    
    def _run_decode(self, noise: np.ndarray, ref_signal_len: np.ndarray) -> np.ndarray:
        """Run decode model to generate final audio"""
        session = self.model_session_manager.sessions['decode']
        input_names = self.model_session_manager.input_names['decode']
        output_names = self.model_session_manager.output_names['decode']
        
        inputs = {
            input_names[0]: noise,
            input_names[1]: ref_signal_len
        }
        
        return session.run(output_names, inputs)[0]
    
    def synthesize(self, text: str,
                   gender: Optional[str] = None,
                   group: Optional[str] = None,
                   area: Optional[str] = None,
                   emotion: Optional[str] = None,
                   output_path: Optional[str] = None,
                   reference_audio: Optional[str] = None,
                   reference_text: Optional[str] = None) -> Tuple[np.ndarray, float]:
        """
        Synthesize speech from text
        
        Args:
            text: Target text to synthesize
            reference_audio: Path to reference audio file (optional, uses default if not provided)
            reference_text: Reference text matching the reference audio (optional, uses default if not provided)
            output_path: Path to save the generated audio (optional)
            
        Returns:
            Tuple of (generated_audio, generation_time)
        """
        start_time = time.time()
        
        ref_audio, ref_text = self.model_session_manager.select_sample(gender, group, area, emotion, reference_audio, reference_text)
        
        try:
            inputs_list = self._prepare_inputs(ref_audio, ref_text, text)
            
            generated_waves = []
            for i, (audio, text_ids, max_duration, time_step) in enumerate(inputs_list):
                print(f"Generating speech for chunk {i+1}/{len(inputs_list)}...")
                
                preprocess_outputs = self._run_preprocess(audio, text_ids, max_duration)
                (noise, rope_cos_q, rope_sin_q, rope_cos_k, rope_sin_k, 
                 cat_mel_text, cat_mel_text_drop, ref_signal_len) = preprocess_outputs
                
                noise, time_step = self._run_transformer_steps(
                    noise, rope_cos_q, rope_sin_q, rope_cos_k, rope_sin_k,
                    cat_mel_text, cat_mel_text_drop, time_step
                )
                
                generated_signal = self._run_decode(noise, ref_signal_len)
                generated_waves.append(generated_signal)
            
            # Concatenate all generated waves with cross-fading
            if len(generated_waves) > 1:
                print(f"Concatenating {len(generated_waves)} chunks with improved cross-fade (duration: {self.config.cross_fade_duration}s)...")
            
            final_wave = self.audio_processor.concatenate_with_crossfade_improved(
                generated_waves, self.config.cross_fade_duration, self.config.sample_rate
            )
            
            generation_time = time.time() - start_time
            
            if output_path:
                self.audio_processor.save_audio(final_wave, output_path, self.config.sample_rate)
                print(f"Audio saved to: {output_path}")
            
            return final_wave, generation_time
            
        except Exception as e:
            raise RuntimeError(f"Speech synthesis failed: {str(e)}")
    
    def validate_configuration(self, reference_audio: Optional[str] = None) -> bool:
        """Validate configuration with reference audio"""
        if reference_audio is None:
            # If no reference audio is provided, configuration is valid
            # since the model will use built-in samples
            print("✅ Configuration valid: Using built-in voice samples")
            return True
        else:
            # Validate with the provided reference audio
            return self.config.validate_with_reference_audio(reference_audio) 