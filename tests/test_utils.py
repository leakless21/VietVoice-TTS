"""
Test utilities and fixtures for VietVoice TTS tests
"""

import unittest
import tempfile
import os
import numpy as np
import soundfile as sf
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestFixtures:
    """Common test fixtures and utilities"""
    
    @staticmethod
    def create_dummy_audio_file(file_path: str, duration: float = 1.0, sample_rate: int = 24000):
        """Create a dummy audio file for testing"""
        samples = int(duration * sample_rate)
        audio_data = np.random.uniform(-0.5, 0.5, samples).astype(np.float32)
        sf.write(file_path, audio_data, sample_rate)
        return file_path
    
    @staticmethod
    def create_dummy_vocab_file(file_path: str, chars: list = None):
        """Create a dummy vocabulary file for testing"""
        if chars is None:
            chars = ['a', 'b', 'c', 'd', 'e', ' ', '.', ',', '!', '?']
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for char in chars:
                f.write(f"{char}\n")
        return file_path
    
    @staticmethod
    def create_mock_model_session_manager():
        """Create a mock ModelSessionManager with common setup"""
        mock_manager = MagicMock()
        mock_manager.vocab_path = "fake_vocab.txt"
        mock_manager.select_sample.return_value = ("ref.wav", "ref text")
        mock_manager.load_models.return_value = None
        mock_manager.get_session.return_value = MagicMock()
        return mock_manager
    
    @staticmethod
    def create_mock_text_processor():
        """Create a mock TextProcessor with common setup"""
        mock_processor = MagicMock()
        mock_processor.clean_text.side_effect = lambda x: x
        mock_processor.calculate_text_length.return_value = 50
        mock_processor.chunk_text.return_value = ["Test text"]
        mock_processor.text_to_indices.return_value = np.array([[1, 2, 3]])
        mock_processor.vocab_size = 100
        return mock_processor
    
    @staticmethod
    def create_mock_audio_processor():
        """Create a mock AudioProcessor with common setup"""
        mock_processor = MagicMock()
        mock_processor.load_audio.return_value = np.zeros((1, 16000), dtype=np.int16)
        mock_processor.concatenate_with_crossfade_improved.return_value = np.zeros(16000, dtype=np.int16)
        mock_processor.save_audio.return_value = None
        mock_processor.normalize_to_int16.side_effect = lambda x: x.astype(np.int16)
        mock_processor.fix_clipped_audio.side_effect = lambda x: x
        return mock_processor


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures = TestFixtures()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def get_temp_file_path(self, filename: str) -> str:
        """Get a temporary file path"""
        return os.path.join(self.temp_dir, filename)
    
    def create_test_audio_file(self, filename: str = "test.wav", duration: float = 1.0) -> str:
        """Create a test audio file and return its path"""
        file_path = self.get_temp_file_path(filename)
        return self.fixtures.create_dummy_audio_file(file_path, duration)
    
    def create_test_vocab_file(self, filename: str = "vocab.txt") -> str:
        """Create a test vocabulary file and return its path"""
        file_path = self.get_temp_file_path(filename)
        return self.fixtures.create_dummy_vocab_file(file_path)
    
    def assert_audio_array_valid(self, audio: np.ndarray):
        """Assert that an audio array is valid"""
        self.assertIsInstance(audio, np.ndarray)
        self.assertGreater(len(audio), 0)
        self.assertTrue(np.isfinite(audio).all())
    
    def assert_duration_valid(self, duration: float):
        """Assert that a duration value is valid"""
        self.assertIsInstance(duration, (int, float))
        self.assertGreater(duration, 0)
        self.assertTrue(np.isfinite(duration))


class MockedComponentsTestCase(BaseTestCase):
    """Test case with pre-mocked TTS components"""
    
    def setUp(self):
        super().setUp()
        
        # Create patches for all major components
        self.model_mgr_patcher = patch('vietvoicetts.core.tts_engine.ModelSessionManager')
        self.text_proc_patcher = patch('vietvoicetts.core.tts_engine.TextProcessor')
        self.audio_proc_patcher = patch('vietvoicetts.core.tts_engine.AudioProcessor')
        
        # Start patches
        self.mock_model_mgr = self.model_mgr_patcher.start()
        self.mock_text_proc = self.text_proc_patcher.start()
        self.mock_audio_proc = self.audio_proc_patcher.start()
        
        # Setup mock instances
        self.mock_model_mgr_instance = self.fixtures.create_mock_model_session_manager()
        self.mock_text_proc_instance = self.fixtures.create_mock_text_processor()
        self.mock_audio_proc_instance = self.fixtures.create_mock_audio_processor()
        
        # Configure mocks to return instances
        self.mock_model_mgr.return_value = self.mock_model_mgr_instance
        self.mock_text_proc.return_value = self.mock_text_proc_instance
        self.mock_audio_proc.return_value = self.mock_audio_proc_instance
    
    def tearDown(self):
        super().tearDown()
        # Stop patches
        self.model_mgr_patcher.stop()
        self.text_proc_patcher.stop()
        self.audio_proc_patcher.stop()


class TestUtilities(unittest.TestCase):
    """Test the test utilities themselves"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures = TestFixtures()
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_dummy_audio_file(self):
        """Test dummy audio file creation"""
        file_path = os.path.join(self.temp_dir, "test.wav")
        result_path = self.fixtures.create_dummy_audio_file(file_path, duration=2.0)
        
        self.assertEqual(result_path, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify audio file properties
        audio_data, sample_rate = sf.read(file_path)
        self.assertAlmostEqual(len(audio_data) / sample_rate, 2.0, places=1)
    
    def test_create_dummy_vocab_file(self):
        """Test dummy vocabulary file creation"""
        file_path = os.path.join(self.temp_dir, "vocab.txt")
        chars = ['x', 'y', 'z']
        result_path = self.fixtures.create_dummy_vocab_file(file_path, chars)
        
        self.assertEqual(result_path, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        # Verify vocab file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip().split('\n')
        self.assertEqual(content, chars)
    
    def test_mock_factories(self):
        """Test mock factory methods"""
        # Test model session manager mock
        mock_mgr = self.fixtures.create_mock_model_session_manager()
        self.assertEqual(mock_mgr.vocab_path, "fake_vocab.txt")
        self.assertEqual(mock_mgr.select_sample.return_value, ("ref.wav", "ref text"))
        
        # Test text processor mock
        mock_text = self.fixtures.create_mock_text_processor()
        self.assertEqual(mock_text.clean_text("test"), "test")
        self.assertEqual(mock_text.calculate_text_length.return_value, 50)
        
        # Test audio processor mock
        mock_audio = self.fixtures.create_mock_audio_processor()
        result = mock_audio.load_audio.return_value
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.int16)
    
    def test_base_test_case(self):
        """Test BaseTestCase functionality"""
        class TestExample(BaseTestCase):
            def test_example(self):
                # Test temp file creation
                audio_path = self.create_test_audio_file("example.wav", 1.5)
                self.assertTrue(os.path.exists(audio_path))
                
                vocab_path = self.create_test_vocab_file("example_vocab.txt")
                self.assertTrue(os.path.exists(vocab_path))
                
                # Test assertions
                audio = np.array([1, 2, 3], dtype=np.float32)
                self.assert_audio_array_valid(audio)
                self.assert_duration_valid(1.23)
        
        # Run the test
        test_instance = TestExample()
        test_instance.setUp()
        try:
            test_instance.test_example()
        finally:
            test_instance.tearDown()


if __name__ == '__main__':
    unittest.main()