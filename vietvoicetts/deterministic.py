"""
Deterministic initialization for VietVoice-TTS
Import this module before any TTS operations to freeze all random seeds.
"""

import os
import random
import numpy as np
import onnxruntime as ort
from loguru import logger

# Fixed seed for reproducible results
DETERMINISTIC_SEED = 9527

def freeze_all_seeds(seed: int = DETERMINISTIC_SEED):
    """
    Freeze all random number generators for deterministic TTS output.
    
    Args:
        seed: Integer seed value (default: 9527)
    """
    # 1. Python's built-in random module
    random.seed(seed)
    
    # 2. NumPy random number generator
    np.random.seed(seed)
    
    # 3. ONNX Runtime random operations
    ort.set_seed(seed)
    
    # 4. Make Python's hash() deterministic across runs
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    logger.info(f"🔒 All random seeds frozen to {seed} for deterministic output")

def setup_deterministic_tts(seed: int = DETERMINISTIC_SEED):
    """
    Complete setup for deterministic TTS inference.
    Call this once at the start of your application.
    
    Args:
        seed: Integer seed value (default: 9527)
    """
    freeze_all_seeds(seed)
    
    # Additional environment variables for deterministic execution
    os.environ["OMP_NUM_THREADS"] = "1"          # Single-threaded execution
    os.environ["MKL_NUM_THREADS"] = "1"          # Intel MKL single-threaded
    
    # GPU determinism (if using CUDA)
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"     # Synchronous CUDA kernels
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"  # Deterministic cuBLAS
    
    logger.info("🎯 Deterministic TTS environment configured")

# Auto-initialize when module is imported
freeze_all_seeds() 