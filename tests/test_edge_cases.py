"""
Comprehensive edge case tests for VietVoice TTS
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os
import numpy as np
from pathlib import Path
import threading
import time

from vietvoicetts.client import TTSApi
from vietvoicetts.core.text_processor import TextProcessor
from vietvoicetts.core.audio_processor import AudioProcessor
from vietvoicetts.core.model_config import ModelConfig


class TestInputValidation(unittest.TestCase):
    """Test input validation edge cases"""
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_empty_text_handling(self, mock_engine):
        """Test handling of empty or whitespace-only text"""
        api = TTSApi()
        
        # Test empty string - should be handled gracefully
        with patch.object(api.engine, 'synthesize') as mock_synthesize:
            mock_synthesize.return_value = (np.array([0.1, 0.2]), 1.0)
            result = api.synthesize("")
            self.assertIsNotNone(result)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_none_text_handling(self, mock_engine):
        """Test handling of None text input"""
        api = TTSApi()
        
        with self.assertRaises(ValueError):
            api.synthesize(None)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_whitespace_only_text(self, mock_engine):
        """Test handling of whitespace-only text"""
        api = TTSApi()
        
        with patch.object(api.engine, 'synthesize') as mock_synthesize:
            mock_synthesize.return_value = (np.array([0.1, 0.2]), 1.0)
            result = api.synthesize("   \n\t  ")
            self.assertIsNotNone(result)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_very_long_text(self, mock_engine):
        """Test handling of extremely long text"""
        api = TTSApi()
        
        # Create text longer than typical limits
        long_text = "This is a very long sentence. " * 1000  # ~30k characters
        
        with patch.object(api.engine, 'synthesize') as mock_synthesize:
            mock_synthesize.return_value = (np.array([0.1, 0.2]), 1.0)
            result = api.synthesize(long_text)
            self.assertIsNotNone(result)
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="a\nb\nc\n")):
                processor = TextProcessor("fake_vocab.txt")
                
                # Test Vietnamese text with diacritics
                vietnamese_text = "Xin chào! Tôi là trợ lý AI. Hôm nay thế nào? 🇻🇳"
                cleaned = processor.clean_text(vietnamese_text)
                self.assertIsInstance(cleaned, str)
                self.assertGreater(len(cleaned), 0)
                
                # Test text with emojis and special characters
                special_text = "Hello 😊 World! @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
                cleaned_special = processor.clean_text(special_text)
                self.assertIsInstance(cleaned_special, str)
                
                # Test mixed scripts
                mixed_text = "English Tiếng Việt 中文 العربية русский"
                cleaned_mixed = processor.clean_text(mixed_text)
                self.assertIsInstance(cleaned_mixed, str)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_invalid_file_paths(self, mock_engine):
        """Test handling of invalid file paths"""
        api = TTSApi()
        
        # Test invalid output path (should raise appropriate error)
        with self.assertRaises((OSError, IOError, PermissionError, FileNotFoundError)):
            api.synthesize_to_file("test", "/invalid/nonexistent/path/output.wav")
        
        # Test path with invalid characters
        with self.assertRaises((OSError, IOError, ValueError)):
            api.synthesize_to_file("test", "invalid\x00filename.wav")


class TestAudioProcessingEdgeCases(unittest.TestCase):
    """Test audio processing edge cases"""
    
    def test_zero_length_audio(self):
        """Test handling of zero-length audio"""
        processor = AudioProcessor()
        
        # Test empty audio array
        empty_audio = np.array([], dtype=np.float32)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            try:
                # Should handle gracefully or raise appropriate error
                with self.assertRaises((ValueError, RuntimeError)):
                    processor.save_audio(empty_audio, tmp.name, 16000)
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
    
    def test_very_short_audio(self):
        """Test handling of very short audio"""
        processor = AudioProcessor()
        
        # Test with single sample
        short_audio = np.array([0.1], dtype=np.float32)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            try:
                processor.save_audio(short_audio, tmp.name, 16000)
                loaded = processor.load_audio(tmp.name, 16000)
                self.assertGreater(len(loaded), 0)
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
    
    def test_audio_with_extreme_values(self):
        """Test audio with extreme values (clipping, NaN, Inf)"""
        processor = AudioProcessor()
        
        # Test with clipped values
        clipped_audio = np.array([5.0, -5.0, 0.5], dtype=np.float32)
        fixed_audio = processor.fix_clipped_audio(clipped_audio)
        self.assertTrue(np.all(np.abs(fixed_audio) <= 1.0))
        
        # Test with NaN values
        nan_audio = np.array([0.1, np.nan, 0.3], dtype=np.float32)
        fixed_nan = processor.fix_clipped_audio(nan_audio)
        self.assertFalse(np.any(np.isnan(fixed_nan)))
        
        # Test with Inf values
        inf_audio = np.array([0.1, np.inf, -np.inf], dtype=np.float32)
        fixed_inf = processor.fix_clipped_audio(inf_audio)
        self.assertFalse(np.any(np.isinf(fixed_inf)))
    
    def test_audio_format_conversion_edge_cases(self):
        """Test audio format conversion edge cases"""
        processor = AudioProcessor()
        
        # Test with different dtypes
        int16_audio = np.array([1000, -1000, 0], dtype=np.int16)
        normalized = processor.normalize_to_int16(int16_audio.astype(np.float32) / 32768.0)
        self.assertEqual(normalized.dtype, np.int16)
        
        # Test with float64
        float64_audio = np.array([0.1, -0.1, 0.0], dtype=np.float64)
        normalized_64 = processor.normalize_to_int16(float64_audio)
        self.assertEqual(normalized_64.dtype, np.int16)


class TestTextProcessingEdgeCases(unittest.TestCase):
    """Test text processing edge cases"""
    
    def test_very_long_text_chunking(self):
        """Test text chunking for very long inputs"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="a\nb\nc\n")):
                processor = TextProcessor("fake_vocab.txt")
                
                # Test very long text
                long_text = "This is a very long text. " * 1000  # ~26k characters
                chunks = processor.chunk_text(long_text, max_length=500)
                
                self.assertGreater(len(chunks), 1)
                for chunk in chunks:
                    self.assertLessEqual(len(chunk), 500)
                
                # Verify all text is preserved
                reconstructed = " ".join(chunks)
                self.assertIn("This is a very long text.", reconstructed)
    
    def test_text_with_no_word_boundaries(self):
        """Test text chunking with no clear word boundaries"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="a\nb\nc\n")):
                processor = TextProcessor("fake_vocab.txt")
                
                # Text with no spaces
                no_spaces = "a" * 1000
                chunks = processor.chunk_text(no_spaces, max_length=100)
                
                self.assertGreater(len(chunks), 1)
                for chunk in chunks:
                    self.assertLessEqual(len(chunk), 100)
    
    def test_empty_vocabulary_handling(self):
        """Test handling of empty or invalid vocabulary"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="")):
                processor = TextProcessor("empty_vocab.txt")
                
                # Should handle empty vocab gracefully
                vocab = processor.load_vocab("empty_vocab.txt")
                self.assertIsInstance(vocab, dict)


class TestConcurrencyAndThreadSafety(unittest.TestCase):
    """Test concurrency and thread safety"""
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_concurrent_synthesis_requests(self, mock_engine):
        """Test thread safety with concurrent synthesis requests"""
        mock_instance = MagicMock()
        mock_instance.synthesize.return_value = (np.array([1, 2, 3]), 1.0)
        mock_engine.return_value = mock_instance
        
        api = TTSApi()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                result = api.synthesize(f"test text {worker_id}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_rapid_sequential_requests(self, mock_engine):
        """Test rapid sequential requests"""
        mock_instance = MagicMock()
        mock_instance.synthesize.return_value = (np.array([1, 2, 3]), 1.0)
        mock_engine.return_value = mock_instance
        
        api = TTSApi()
        
        # Make rapid sequential requests
        for i in range(50):
            result = api.synthesize(f"rapid test {i}")
            self.assertIsNotNone(result)


class TestResourceManagement(unittest.TestCase):
    """Test resource management and cleanup"""
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_memory_cleanup_context_manager(self, mock_engine):
        """Test proper memory cleanup with context manager"""
        mock_instance = MagicMock()
        mock_engine.return_value = mock_instance
        
        # Test context manager usage
        with TTSApi() as api:
            self.assertIsNotNone(api)
            # Access engine to initialize it
            _ = api.engine
        
        # Cleanup should have been called
        mock_instance.cleanup.assert_called_once()
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_explicit_cleanup(self, mock_engine):
        """Test explicit cleanup"""
        mock_instance = MagicMock()
        mock_engine.return_value = mock_instance
        
        api = TTSApi()
        _ = api.engine  # Initialize engine
        api.cleanup()
        
        mock_instance.cleanup.assert_called_once()
    
    def test_temporary_file_cleanup(self):
        """Test that temporary files are properly cleaned up"""
        with patch('vietvoicetts.client.TTSEngine') as mock_engine:
            mock_instance = MagicMock()
            mock_instance.synthesize.return_value = (np.array([1, 2, 3]), 1.0)
            mock_engine.return_value = mock_instance
            
            api = TTSApi()
            
            # Mock the file operations to track temp files
            temp_files_created = []
            
            def mock_tempfile(*args, **kwargs):
                temp_file = tempfile.NamedTemporaryFile(*args, **kwargs)
                temp_files_created.append(temp_file.name)
                return temp_file
            
            with patch('tempfile.NamedTemporaryFile', side_effect=mock_tempfile):
                with patch('builtins.open', mock_open(read_data=b'fake_wav_data')):
                    result = api.synthesize_to_bytes("test")
                    self.assertIsNotNone(result)
            
            # Verify temp files were cleaned up
            for temp_file in temp_files_created:
                self.assertFalse(os.path.exists(temp_file))


class TestModelConfigurationEdgeCases(unittest.TestCase):
    """Test model configuration edge cases"""
    
    def test_extreme_configuration_values(self):
        """Test model configuration with extreme values"""
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            # Test with very slow speed
            config = ModelConfig(speed=0.01)
            self.assertEqual(config.speed, 0.01)
            
            # Test with very fast speed
            config_fast = ModelConfig(speed=10.0)
            self.assertEqual(config_fast.speed, 10.0)
            
            # Test with minimal NFE steps
            config_min_nfe = ModelConfig(nfe_step=1)
            self.assertEqual(config_min_nfe.nfe_step, 1)
            
            # Test with zero crossfade
            config_no_crossfade = ModelConfig(cross_fade_duration=0.0)
            self.assertEqual(config_no_crossfade.cross_fade_duration, 0.0)
    
    def test_invalid_configuration_combinations(self):
        """Test invalid configuration combinations"""
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            # Test negative values
            with self.assertRaises((ValueError, AssertionError)):
                ModelConfig(speed=-1.0)
            
            with self.assertRaises((ValueError, AssertionError)):
                ModelConfig(nfe_step=0)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery mechanisms"""
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_engine_initialization_retry(self, mock_engine):
        """Test engine initialization failure recovery"""
        # First call fails, second succeeds
        mock_engine.side_effect = [Exception("First failure"), MagicMock()]
        
        api = TTSApi()
        
        # First access should fail
        with self.assertRaises(Exception):
            _ = api.engine
        
        # Reset the mock to succeed
        mock_engine.side_effect = None
        mock_engine.return_value = MagicMock()
        
        # Should be able to retry
        api._engine = None  # Reset internal state
        engine = api.engine
        self.assertIsNotNone(engine)
    
    @patch('vietvoicetts.client.TTSEngine')
    def test_synthesis_error_handling(self, mock_engine):
        """Test synthesis error handling and recovery"""
        mock_instance = MagicMock()
        mock_instance.synthesize.side_effect = [
            Exception("Synthesis failed"),
            (np.array([1, 2, 3]), 1.0)  # Second call succeeds
        ]
        mock_engine.return_value = mock_instance
        
        api = TTSApi()
        
        # First call should fail
        with self.assertRaises(Exception):
            api.synthesize("test")
        
        # Second call should succeed
        result = api.synthesize("test")
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()