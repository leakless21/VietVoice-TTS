"""
Model session management for ONNX Runtime
"""

import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import json
import onnxruntime
import random
from loguru import logger

from .model_config import ModelConfig, MODEL_GENDER, MODEL_GROUP, MODEL_AREA, MODEL_EMOTION


class ModelSessionManager:
    """Manages ONNX Runtime sessions"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.providers = self._get_optimal_providers()
        self.sessions = {}
        self.input_names = {}
        self.output_names = {}
        self.sample_metadata = {}
        self.temp_dir = None
        self.vocab_path = None
        
    def _get_optimal_providers(self) -> List[str]:
        """Get the fastest available providers"""
        available_providers = onnxruntime.get_available_providers()
        
        provider_priority = [
            'CUDAExecutionProvider',
            'CPUExecutionProvider'
        ]
        
        selected_providers = []
        for provider in provider_priority:
            if provider in available_providers:
                selected_providers.append(provider)
        
        if 'CPUExecutionProvider' not in selected_providers:
            selected_providers.append('CPUExecutionProvider')
        
        return selected_providers
    
    def _create_session_options(self) -> onnxruntime.SessionOptions:
        """Create optimized ONNX Runtime session options"""
        session_opts = onnxruntime.SessionOptions()
        session_opts.log_severity_level = self.config.log_severity_level
        session_opts.log_verbosity_level = self.config.log_verbosity_level
        session_opts.inter_op_num_threads = self.config.inter_op_num_threads
        session_opts.intra_op_num_threads = self.config.intra_op_num_threads
        session_opts.enable_cpu_mem_arena = self.config.enable_cpu_mem_arena
        session_opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        session_opts.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_opts.add_session_config_entry("session.intra_op.allow_spinning", "1")
        session_opts.add_session_config_entry("session.inter_op.allow_spinning", "1")
        session_opts.add_session_config_entry("session.set_denormal_as_zero", "1")
        return session_opts
    
    def _load_models_from_file(self) -> None:
        """Load ONNX models from downloaded model file and extract vocab"""
        # Ensure model is downloaded and get path
        model_path = self.config.ensure_model_downloaded()
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        expected_models = {
            'preprocess': 'preprocess.onnx',
            'transformer': 'transformer.onnx', 
            'decode': 'decode.onnx'
        }
        
        try:
            with tarfile.open(model_path, 'r') as tar:
                tar_members = tar.getnames()
                
                # Load metadata.json
                self.sample_metadata = json.load(tar.extractfile("audio_metadata.json"))
                
                # Load ONNX models
                for model_name, filename in expected_models.items():
                    matching_member = next((m for m in tar_members if m.endswith(filename)), None)
                    if not matching_member:
                        raise FileNotFoundError(f"Model file '{filename}' not found in model archive")
                    
                    extracted_file = tar.extractfile(matching_member)
                    if not extracted_file:
                        raise RuntimeError(f"Failed to extract {filename} from model archive")
                    
                    model_bytes = extracted_file.read()
                    session_opts = self._create_session_options()
                    session = onnxruntime.InferenceSession(
                        model_bytes,
                        sess_options=session_opts,
                        providers=self.providers
                    )
                    
                    self.sessions[model_name] = session
                    self.input_names[model_name] = [inp.name for inp in session.get_inputs()]
                    self.output_names[model_name] = [out.name for out in session.get_outputs()]
                
                # Extract vocab.txt to temporary file
                vocab_member = next((m for m in tar_members if m.endswith('vocab.txt')), None)
                if not vocab_member:
                    raise FileNotFoundError("Vocabulary file 'vocab.txt' not found in model archive")
                
                self.temp_dir = tempfile.mkdtemp(prefix="tts_vocab_")
                vocab_temp_path = Path(self.temp_dir) / 'vocab.txt'
                
                extracted_file = tar.extractfile(vocab_member)
                if not extracted_file:
                    raise RuntimeError("Failed to extract vocab.txt from model archive")
                
                with open(vocab_temp_path, 'wb') as f:
                    f.write(extracted_file.read())
                
                self.vocab_path = str(vocab_temp_path)
                
        except Exception as e:
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            raise RuntimeError(f"Failed to load models from file: {str(e)}")
    
    def load_models(self) -> None:
        """Load all ONNX models from downloaded model file"""
        onnxruntime.set_seed(self.config.random_seed)
        random.seed(self.config.random_seed)
        self._load_models_from_file()
    
    def select_sample(self, gender: Optional[str] = None,
                     group: Optional[str] = None,
                     area: Optional[str] = None,
                     emotion: Optional[str] = None,
                     sample_iteration: Optional[int] = None,
                     reference_audio: Optional[str] = None,
                     reference_text: Optional[str] = None) -> Tuple[str, str]:
        """Select a sample from the metadata"""
        filter_options = {}
        if gender is not None:
            if gender not in MODEL_GENDER:
                raise ValueError(f"Invalid gender: {gender}. Must be one of {MODEL_GENDER}")
            filter_options["gender"] = gender
        if group is not None:
            if group not in MODEL_GROUP:
                raise ValueError(f"Invalid group: {group}. Must be one of {MODEL_GROUP}")
            filter_options["group"] = group
        if area is not None:
            if area not in MODEL_AREA:
                raise ValueError(f"Invalid area: {area}. Must be one of {MODEL_AREA}")
            filter_options["area"] = area
        if emotion is not None:
            if emotion not in MODEL_EMOTION:
                raise ValueError(f"Invalid emotion: {emotion}. Must be one of {MODEL_EMOTION}")
            filter_options["emotion"] = emotion
        
        if reference_audio is not None:
            if reference_text is None:
                raise ValueError("Reference text is required when using reference audio")
            if not Path(reference_audio).exists():
                raise FileNotFoundError(f"Reference audio file not found: {reference_audio}")
            if len(filter_options) > 0:
                raise ValueError(f"Cannot use reference audio and text with options: {list(filter_options.keys())}")
            logger.info(f"Using reference audio and text: {reference_audio}")
            return reference_audio, reference_text

        try:
            available_samples = []

            if len(filter_options) == 0:
                available_samples = [(sample, idx) for idx, sample in enumerate(self.sample_metadata)]
            else:
                for idx, sample in enumerate(self.sample_metadata):
                    if all(sample[key] == value for key, value in filter_options.items()):
                        available_samples.append((sample, idx))
            
            if len(available_samples) == 0:
                sample, sample_idx = self.sample_metadata[0], 0
            else:
                # Use sample_iteration to choose which available sample to use
                if sample_iteration is not None:
                    if sample_iteration >= len(available_samples):
                        raise ValueError(f"sample_iteration {sample_iteration} is out of range. Only {len(available_samples)} samples available for the given filters.")
                    sample, sample_idx = available_samples[sample_iteration]
                    logger.info(f"Using sample iteration {sample_iteration} out of {len(available_samples)} available samples")
                else:
                    sample, sample_idx = available_samples[0]

            logger.info(f"Selected sample #{sample_idx} with gender: {sample['gender']}, group: {sample['group']}, area: {sample['area']}, emotion: {sample['emotion']}")

            # Get the cached model path
            model_path = self.config.ensure_model_downloaded()
            
            with tarfile.open(model_path, 'r') as tar:
                ref_audio = tar.extractfile("cleaned_audios/" + sample["file_name"])
                if not ref_audio:
                    raise FileNotFoundError(f"Audio file {sample['file_name']} not found in model archive")
                ref_audio = ref_audio.read()
                ref_text = sample["text"]
        except KeyError:
            raise ValueError(f"Sample not found for gender: {gender}, group: {group}, area: {area}, emotion: {emotion}")
        return ref_audio, ref_text
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
            self.vocab_path = None
    
    def __del__(self):
        self.cleanup() 