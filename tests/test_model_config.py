"""
Comprehensive tests for ModelConfig class
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os
from pathlib import Path
from vietvoicetts.core.model_config import ModelConfig, MODEL_GENDER, MODEL_GROUP, MODEL_AREA, MODEL_EMOTION


class TestModelConfig(unittest.TestCase):
    
    def test_default_initialization(self):
        """Test ModelConfig with default values"""
        config = ModelConfig()
        self.assertEqual(config.nfe_step, 32)
        self.assertEqual(config.speed, 0.9)
        self.assertEqual(config.random_seed, 9527)
        self.assertEqual(config.sample_rate, 24000)
        self.assertEqual(config.cross_fade_duration, 0.1)
        self.assertEqual(config.max_chunk_duration, 15.0)
        self.assertEqual(config.min_target_duration, 1.0)
    
    def test_custom_initialization(self):
        """Test ModelConfig with custom values"""
        config = ModelConfig(
            speed=1.2,
            random_seed=12345,
            nfe_step=64,
            cross_fade_duration=0.2
        )
        self.assertEqual(config.speed, 1.2)
        self.assertEqual(config.random_seed, 12345)
        self.assertEqual(config.nfe_step, 64)
        self.assertEqual(config.cross_fade_duration, 0.2)
    
    def test_model_path_property(self):
        """Test model_path property"""
        config = ModelConfig(model_cache_dir="test_models", model_filename="test.pt")
        expected_path = str(Path("test_models").expanduser() / "test.pt")
        self.assertEqual(config.model_path, expected_path)
    
    @patch('vietvoicetts.core.model_config.ModelConfig.validate_paths')
    @patch('urllib.request.urlretrieve')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_ensure_model_downloaded_new_download(self, mock_mkdir, mock_exists, mock_urlretrieve, mock_validate):
        """Test downloading model when it doesn't exist"""
        mock_exists.return_value = False
        mock_validate.return_value = None  # Skip validation during init
        config = ModelConfig()
        
        with patch('builtins.print'):
            result = config.ensure_model_downloaded()
        
        mock_urlretrieve.assert_called_once()
        self.assertEqual(result, config.model_path)
    
    @patch('pathlib.Path.exists')
    def test_ensure_model_downloaded_cached(self, mock_exists):
        """Test using cached model when it exists"""
        mock_exists.return_value = True
        config = ModelConfig()
        
        with patch('builtins.print'):
            result = config.ensure_model_downloaded()
        
        self.assertEqual(result, config.model_path)
    
    @patch('vietvoicetts.core.model_config.ModelConfig.validate_paths')
    @patch('urllib.request.urlretrieve')
    @patch('pathlib.Path.exists')
    def test_ensure_model_downloaded_failure(self, mock_exists, mock_urlretrieve, mock_validate):
        """Test handling download failure"""
        mock_exists.return_value = False
        mock_urlretrieve.side_effect = Exception("Download failed")
        mock_validate.return_value = None  # Skip validation during init
        config = ModelConfig()
        
        with self.assertRaises(RuntimeError):
            config.ensure_model_downloaded()
    
    @patch('vietvoicetts.core.model_config.ModelConfig.validate_paths')
    def test_validate_paths_success(self, mock_validate):
        """Test successful path validation"""
        mock_validate.return_value = None
        config = ModelConfig()
        # Should not raise exception during init
        self.assertIsNotNone(config)
    
    @patch('vietvoicetts.core.model_config.ModelConfig.ensure_model_downloaded')
    def test_validate_paths_failure(self, mock_ensure_model):
        """Test path validation failure"""
        mock_ensure_model.side_effect = Exception("Model not found")
        
        with self.assertRaises(RuntimeError):
            ModelConfig()
    
    @patch('pydub.AudioSegment.from_file')
    def test_validate_with_reference_audio_valid(self, mock_from_file):
        """Test reference audio validation with valid configuration"""
        mock_audio = MagicMock()
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.__len__ = MagicMock(return_value=5000)  # 5 seconds
        mock_from_file.return_value = mock_audio
        
        config = ModelConfig(max_chunk_duration=20.0)
        
        with patch('builtins.print'):
            result = config.validate_with_reference_audio("test.wav")
        
        self.assertTrue(result)
    
    @patch('pydub.AudioSegment.from_file')
    def test_validate_with_reference_audio_invalid(self, mock_from_file):
        """Test reference audio validation with invalid configuration"""
        mock_audio = MagicMock()
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.__len__ = MagicMock(return_value=15000)  # 15 seconds
        mock_from_file.return_value = mock_audio
        
        config = ModelConfig(max_chunk_duration=10.0)  # Too small
        
        with patch('builtins.print'):
            result = config.validate_with_reference_audio("test.wav")
        
        self.assertFalse(result)
    
    def test_from_dict(self):
        """Test creating config from dictionary"""
        config_dict = {
            'speed': 1.5,
            'random_seed': 54321,
            'nfe_step': 64
        }
        config = ModelConfig.from_dict(config_dict)
        self.assertEqual(config.speed, 1.5)
        self.assertEqual(config.random_seed, 54321)
        self.assertEqual(config.nfe_step, 64)
    
    def test_to_dict(self):
        """Test converting config to dictionary"""
        config = ModelConfig(speed=1.2, random_seed=12345)
        config_dict = config.to_dict()
        self.assertEqual(config_dict['speed'], 1.2)
        self.assertEqual(config_dict['random_seed'], 12345)
        self.assertIn('nfe_step', config_dict)
    
    def test_model_constants(self):
        """Test model constants are properly defined"""
        self.assertIn("male", MODEL_GENDER)
        self.assertIn("female", MODEL_GENDER)
        self.assertIn("story", MODEL_GROUP)
        self.assertIn("northern", MODEL_AREA)
        self.assertIn("neutral", MODEL_EMOTION)


if __name__ == '__main__':
    unittest.main()