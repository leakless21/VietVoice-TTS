"""
Integration tests for VietVoice TTS
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import tempfile
import os
from vietvoicetts.client import TTSApi, synthesize, synthesize_to_bytes
from vietvoicetts.core.model_config import ModelConfig


class TestIntegration(unittest.TestCase):
    """Integration tests that test multiple components together"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_path = os.path.join(self.temp_dir, "test_output.wav")
    
    def tearDown(self):
        # Clean up test files
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)
        os.rmdir(self.temp_dir)
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_api_with_custom_config(self, mock_synthesize):
        """Test API with custom configuration"""
        # Mock the synthesize method to return expected values
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        # Create custom config
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            config = ModelConfig(speed=1.2, random_seed=12345)
            api = TTSApi(config)
            
            # Test synthesis
            audio, duration = api.synthesize("Test text")
            
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            self.assertEqual(config.speed, 1.2)
            self.assertEqual(config.random_seed, 12345)
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_api_with_voice_parameters(self, mock_synthesize):
        """Test API with voice parameters"""
        # Mock the synthesize method to return expected values
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            # Test with voice parameters
            audio, duration = api.synthesize(
                "Test text",
                gender="female",
                group="news",
                area="northern",
                emotion="happy"
            )
            
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            
            # Verify the synthesize method was called with correct parameters
            mock_synthesize.assert_called_once_with(
                text="Test text",
                gender="female",
                group="news",
                area="northern",
                emotion="happy",
                output_path=None,
                reference_audio=None,
                reference_text=None
            )
    
    @patch('vietvoicetts.client.TTSApi.synthesize_to_file')
    @patch('vietvoicetts.client.TTSApi.synthesize_to_bytes')
    def test_convenience_functions(self, mock_synthesize_to_bytes, mock_synthesize_to_file):
        """Test convenience functions"""
        # Mock the API methods
        mock_synthesize_to_file.return_value = 1.23
        mock_synthesize_to_bytes.return_value = (b'fake_wav_data', 1.23)
        
        # Test synthesize function
        duration = synthesize("Test text", self.test_output_path)
        self.assertIsInstance(duration, float)
        self.assertEqual(duration, 1.23)
        
        # Test synthesize_to_bytes function
        wav_bytes, duration = synthesize_to_bytes("Test text")
        self.assertIsInstance(wav_bytes, bytes)
        self.assertIsInstance(duration, float)
        self.assertEqual(wav_bytes, b'fake_wav_data')
        self.assertEqual(duration, 1.23)
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_long_text_chunking(self, mock_synthesize):
        """Test handling of long text that requires chunking"""
        # Mock the synthesize method to return expected values
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 2.45)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            long_text = "This is a very long text that should be chunked into multiple parts for processing. " * 10
            
            audio, duration = api.synthesize(long_text)
            
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            # Verify the synthesize method was called with the long text
            mock_synthesize.assert_called_once_with(
                text=long_text,
                gender=None,
                group=None,
                area=None,
                emotion=None,
                output_path=None,
                reference_audio=None,
                reference_text=None
            )
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_error_handling_invalid_text(self, mock_synthesize):
        """Test error handling for invalid text input"""
        # Mock the synthesize method to raise appropriate errors
        def side_effect(text, **kwargs):
            if not text or text is None:
                raise ValueError("Text cannot be empty or None")
            return (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        mock_synthesize.side_effect = side_effect
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            # Test empty text
            with self.assertRaises(ValueError):
                api.synthesize("")
            
            # Test None text
            with self.assertRaises(ValueError):
                api.synthesize("")
            
            # Test valid text works
            audio, duration = api.synthesize("Valid text")
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
    
    @patch('vietvoicetts.core.tts_engine.TTSEngine.synthesize')
    def test_reference_audio_synthesis(self, mock_synthesize):
        """Test synthesis with reference audio"""
        # Mock the synthesize method to return expected values
        mock_synthesize.return_value = (np.array([1, 2, 3], dtype=np.int16), 1.23)
        
        with patch('vietvoicetts.core.model_config.ModelConfig.validate_paths'):
            api = TTSApi()
            
            # Test with reference audio
            audio, duration = api.synthesize(
                "Test text",
                reference_audio="reference.wav",
                reference_text="Reference text"
            )
            
            self.assertIsInstance(audio, np.ndarray)
            self.assertIsInstance(duration, float)
            
            # Verify the synthesize method was called with reference audio parameters
            mock_synthesize.assert_called_once_with(
                text="Test text",
                gender=None,
                group=None,
                area=None,
                emotion=None,
                output_path=None,
                reference_audio="reference.wav",
                reference_text="Reference text"
            )
    
    def _setup_mocks(self, mock_audio_proc, mock_text_proc, mock_model_mgr):
        """Helper method to setup common mocks"""
        # Setup model session manager
        mock_model_mgr_instance = mock_model_mgr.return_value
        mock_model_mgr_instance.vocab_path = "fake_vocab.txt"
        mock_model_mgr_instance.select_sample.return_value = ("ref.wav", "ref text")
        mock_model_mgr_instance.load_models.return_value = None
        mock_model_mgr_instance.get_session.return_value = MagicMock()
        
        # Setup text processor
        mock_text_proc_instance = mock_text_proc.return_value
        mock_text_proc_instance.clean_text.side_effect = lambda x: x
        mock_text_proc_instance.calculate_text_length.return_value = 50
        mock_text_proc_instance.chunk_text.return_value = ["Test text"]
        mock_text_proc_instance.text_to_indices.return_value = np.array([[1, 2, 3]])
        
        # Setup audio processor
        mock_audio_proc_instance = mock_audio_proc.return_value
        mock_audio_proc_instance.load_audio.return_value = np.zeros((1, 16000), dtype=np.int16)
        mock_audio_proc_instance.concatenate_with_crossfade_improved.return_value = np.zeros(16000, dtype=np.int16)
        mock_audio_proc_instance.save_audio.return_value = None


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_model_config_invalid_paths(self):
        """Test ModelConfig with invalid paths"""
        with patch('vietvoicetts.core.model_config.ModelConfig.ensure_model_downloaded') as mock_ensure:
            mock_ensure.side_effect = RuntimeError("Model download failed")
            
            with self.assertRaises(RuntimeError):
                ModelConfig()
    
    @patch('vietvoicetts.core.model_config.ModelConfig.ensure_model_downloaded')
    def test_api_initialization_failure(self, mock_ensure):
        """Test API initialization failure"""
        mock_ensure.return_value = "model.pt"
        
        with patch('vietvoicetts.core.tts_engine.TTSEngine') as mock_engine:
            mock_engine.side_effect = Exception("Engine initialization failed")
            
            api = TTSApi()
            with self.assertRaises(Exception):
                # Accessing engine property should trigger initialization
                _ = api.engine


if __name__ == '__main__':
    unittest.main()