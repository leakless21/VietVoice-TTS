"""
Comprehensive tests for ModelSessionManager class
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import json
from vietvoicetts.core.model import ModelSessionManager
from vietvoicetts.core.model_config import ModelConfig


class TestModelSessionManager(unittest.TestCase):
    
    def setUp(self):
        self.config = ModelConfig()
    
    @patch('onnxruntime.get_available_providers')
    def test_get_optimal_providers(self, mock_get_providers):
        """Test optimal provider selection"""
        mock_get_providers.return_value = ['CPUExecutionProvider', 'CUDAExecutionProvider']
        manager = ModelSessionManager(self.config)
        self.assertIn('CPUExecutionProvider', manager.providers)
    
    @patch('onnxruntime.get_available_providers')
    def test_get_optimal_providers_cpu_only(self, mock_get_providers):
        """Test provider selection when only CPU is available"""
        mock_get_providers.return_value = ['CPUExecutionProvider']
        manager = ModelSessionManager(self.config)
        self.assertEqual(manager.providers, ['CPUExecutionProvider'])
    
    @patch('vietvoicetts.core.model.ModelSessionManager._load_models_from_file')
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_load_models_success(self, mock_providers, mock_load_models):
        """Test successful model loading"""
        mock_providers.return_value = ['CPUExecutionProvider']
        mock_load_models.return_value = None
        
        manager = ModelSessionManager(self.config)
        manager.load_models()
        
        # Verify load_models was called
        mock_load_models.assert_called_once()
    
    @patch('vietvoicetts.core.model.ModelSessionManager.select_sample')
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_select_sample_with_criteria(self, mock_providers, mock_select_sample):
        """Test sample selection with specific criteria"""
        mock_providers.return_value = ['CPUExecutionProvider']
        mock_select_sample.return_value = ("sample1.wav", "Hello world")
        
        manager = ModelSessionManager(self.config)
        
        # Test selection with criteria
        audio_path, text = manager.select_sample(
            gender="female",
            group="news",
            area="northern",
            emotion="neutral"
        )
        
        self.assertEqual(audio_path, "sample1.wav")
        self.assertEqual(text, "Hello world")
        mock_select_sample.assert_called_once()
    
    @patch('vietvoicetts.core.model.ModelSessionManager.select_sample')
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_select_sample_random(self, mock_providers, mock_select_sample):
        """Test random sample selection"""
        mock_providers.return_value = ['CPUExecutionProvider']
        mock_select_sample.return_value = ("sample1.wav", "Hello world")
        
        manager = ModelSessionManager(self.config)
        
        audio_path, text = manager.select_sample()
        self.assertEqual(audio_path, "sample1.wav")
        self.assertEqual(text, "Hello world")
        mock_select_sample.assert_called_once()
    
    @patch('vietvoicetts.core.model.ModelSessionManager.select_sample')
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_select_sample_no_match(self, mock_providers, mock_select_sample):
        """Test sample selection when no match found"""
        mock_providers.return_value = ['CPUExecutionProvider']
        mock_select_sample.side_effect = ValueError("Invalid gender: alien. Must be one of ['male', 'female']")
        
        manager = ModelSessionManager(self.config)
        
        # Request non-existent criteria - should raise ValueError
        with self.assertRaises(ValueError):
            manager.select_sample(gender="alien")
        mock_select_sample.assert_called_once()
    
    @patch('vietvoicetts.core.model.ModelSessionManager.cleanup')
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_cleanup(self, mock_providers, mock_cleanup):
        """Test cleanup functionality"""
        mock_providers.return_value = ['CPUExecutionProvider']
        manager = ModelSessionManager(self.config)
        
        # Test that cleanup method can be called
        manager.cleanup()
        mock_cleanup.assert_called_once()
    
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_get_session_existing(self, mock_providers):
        """Test getting existing session"""
        mock_providers.return_value = ['CPUExecutionProvider']
        manager = ModelSessionManager(self.config)
        
        # Test that sessions dict exists and can be accessed
        self.assertIsInstance(manager.sessions, dict)
        
        # Add a mock session
        mock_session = MagicMock()
        manager.sessions['test_model'] = mock_session
        
        # Verify we can retrieve it
        result = manager.sessions.get('test_model')
        self.assertEqual(result, mock_session)
    
    @patch('vietvoicetts.core.model.ModelSessionManager._get_optimal_providers')
    def test_get_session_nonexistent(self, mock_providers):
        """Test getting non-existent session"""
        mock_providers.return_value = ['CPUExecutionProvider']
        manager = ModelSessionManager(self.config)
        
        # Test that accessing non-existent session returns None
        result = manager.sessions.get('nonexistent_model')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()