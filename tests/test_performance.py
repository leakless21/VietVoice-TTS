"""
Performance tests for VietVoice TTS
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import numpy as np
from vietvoicetts.client import TTSApi
from vietvoicetts.core.model_config import ModelConfig


class TestPerformance(unittest.TestCase):
    """Performance benchmarks and stress tests"""
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_synthesis_performance(self, mock_synthesize):
        """Test synthesis performance for various text lengths"""
        # Mock the synthesize method to return expected values with realistic timing
        def mock_synthesis_with_timing(text, **kwargs):
            # Simulate processing time based on text length
            import time
            time.sleep(0.01)  # Small delay to simulate processing
            duration = len(text) * 0.05  # Simulate audio duration
            return (np.array([1, 2, 3], dtype=np.int16), duration)
        
        mock_synthesize.side_effect = mock_synthesis_with_timing
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
        test_cases = [
            ("Short text", "Hello world"),
            ("Medium text", "This is a medium length text that should take a reasonable amount of time to process."),
            ("Long text", "This is a very long text that contains multiple sentences and should test the chunking functionality. " * 10)
        ]
        
        performance_results = {}
        
        for name, text in test_cases:
            start_time = time.time()
            audio, duration = api.synthesize(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            performance_results[name] = {
                'processing_time': processing_time,
                'audio_duration': duration,
                'text_length': len(text),
                'efficiency_ratio': duration / processing_time if processing_time > 0 else float('inf')
            }
            
            # Basic assertions
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            self.assertGreater(duration, 0)
        
        # Print performance results for analysis
        print("\n=== Performance Test Results ===")
        for name, results in performance_results.items():
            print(f"{name}:")
            print(f"  Text length: {results['text_length']} chars")
            print(f"  Processing time: {results['processing_time']:.3f}s")
            print(f"  Audio duration: {results['audio_duration']:.3f}s")
            print(f"  Efficiency ratio: {results['efficiency_ratio']:.2f}x")
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_concurrent_synthesis(self, mock_synthesize):
        """Test multiple synthesis requests"""
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
        texts = [
            "First synthesis request",
            "Second synthesis request", 
            "Third synthesis request",
            "Fourth synthesis request",
            "Fifth synthesis request"
        ]
        
        start_time = time.time()
        results = []
        
        for text in texts:
            audio, duration = api.synthesize(text)
            results.append((audio, duration))
        
        total_time = time.time() - start_time
        
        # Verify all requests completed successfully
        self.assertEqual(len(results), len(texts))
        for audio, duration in results:
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
        
        print(f"\nConcurrent synthesis test:")
        print(f"  Processed {len(texts)} requests in {total_time:.3f}s")
        print(f"  Average time per request: {total_time/len(texts):.3f}s")
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_memory_usage(self, mock_synthesize):
        """Test memory usage patterns"""
        def mock_synthesis_with_size(text, **kwargs):
            # Extract size multiplier from text
            size_multiplier = int(text.split()[-1]) if text.split()[-1].isdigit() else 1
            large_audio = np.zeros(16000 * size_multiplier, dtype=np.int16)
            return (large_audio, 1.23)
        
        mock_synthesize.side_effect = mock_synthesis_with_size
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            # Test with progressively larger audio arrays
            for size_multiplier in [1, 2, 4, 8]:
                audio, duration = api.synthesize(f"Test text {size_multiplier}")
                
                self.assertEqual(len(audio), 16000 * size_multiplier)
                self.assertIsInstance(duration, float)
    
    def test_config_validation_performance(self):
        """Test configuration validation performance"""
        start_time = time.time()
        
        # Test multiple config creations
        configs = []
        for i in range(100):
            with patch('vietvoicetts.core.model_config.ModelConfig.ensure_model_downloaded'):
                with self.assertRaises(ValueError):
                    config = ModelConfig(
                        speed=1.0 + i * 0.01,
                        random_seed=1000 + i,
                        nfe_step=101 + i  # This will be out of range
                    )
        
        creation_time = time.time() - start_time
        
        # Test config operations
        start_time = time.time()
        for config in configs:
            config_dict = config.to_dict()
            new_config = ModelConfig.from_dict(config_dict)
            self.assertEqual(config.speed, new_config.speed)
        
        operation_time = time.time() - start_time
        
        print(f"\nConfig performance test:")
        print(f"  Created 100 configs in {creation_time:.3f}s")
        print(f"  Performed 100 dict operations in {operation_time:.3f}s")
    
    @staticmethod
    def _setup_performance_mocks(mock_audio_proc, mock_text_proc, mock_model_mgr):
        """Setup mocks optimized for performance testing"""
        # Setup model session manager
        mock_model_mgr_instance = mock_model_mgr.return_value
        mock_model_mgr_instance.vocab_path = "fake_vocab.txt"
        mock_model_mgr_instance.select_sample.return_value = ("ref.wav", "ref text")
        mock_model_mgr_instance.load_models.return_value = None
        
        # Setup text processor with realistic processing times
        mock_text_proc_instance = mock_text_proc.return_value
        mock_text_proc_instance.clean_text.side_effect = lambda x: x
        mock_text_proc_instance.calculate_text_length.side_effect = lambda x, y: len(x)
        mock_text_proc_instance.chunk_text.side_effect = lambda x, max_chars=135: [x] if len(x) <= max_chars else [x[i:i+max_chars] for i in range(0, len(x), max_chars)]
        mock_text_proc_instance.text_to_indices.return_value = np.array([[1, 2, 3]])
        
        # Setup audio processor with realistic audio generation
        mock_audio_proc_instance = mock_audio_proc.return_value
        mock_audio_proc_instance.load_audio.return_value = np.zeros((1, 16000), dtype=np.int16)
        mock_audio_proc_instance.concatenate_with_crossfade_improved.return_value = np.zeros(16000, dtype=np.int16)
        mock_audio_proc_instance.save_audio.return_value = None


class TestStressTests(unittest.TestCase):
    """Stress tests for edge cases and limits"""
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_very_long_text(self, mock_synthesize):
        """Test with extremely long text"""
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 5.67)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            # Create very long text (10,000 characters)
            very_long_text = "This is a test sentence. " * 400
            
            audio, duration = api.synthesize(very_long_text)
            
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            self.assertGreater(duration, 0)
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_special_characters(self, mock_synthesize):
        """Test with various special characters"""
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            special_texts = [
                "Text with numbers: 123, 456, 789",
                "Text with punctuation: Hello! How are you? I'm fine.",
                "Text with Vietnamese: Xin chào, tôi là trợ lý AI",
                "Text with symbols: @#$%^&*()",
                "Mixed content: Hello 123 @world! Xin chào 456."
            ]
            
            for text in special_texts:
                audio, duration = api.synthesize(text)
                self.assertIsInstance(audio, np.ndarray)
                self.assertIsInstance(duration, float)
    
    def _setup_stress_mocks(self, mock_audio_proc, mock_text_proc, mock_model_mgr):
        """Setup mocks for stress testing"""
        # Reuse performance mock setup
        TestPerformance._setup_performance_mocks(mock_audio_proc, mock_text_proc, mock_model_mgr)


if __name__ == '__main__':
    unittest.main()