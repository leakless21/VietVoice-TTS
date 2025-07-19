
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from vietvoicetts.core.tts_engine import TTSEngine

class TestTTSEngine(unittest.TestCase):
    @patch('vietvoicetts.core.tts_engine.TextProcessor')
    @patch('vietvoicetts.core.tts_engine.AudioProcessor')
    @patch('vietvoicetts.core.tts_engine.ModelSessionManager')
    def test_synthesize(self, mock_model_session_manager, mock_audio_processor, mock_text_processor):
        # Arrange
        mock_text_processor_instance = MagicMock()
        mock_text_processor.return_value = mock_text_processor_instance
        mock_audio_processor_instance = MagicMock()
        mock_audio_processor.return_value = mock_audio_processor_instance
        mock_model_session_manager_instance = MagicMock()
        mock_model_session_manager.return_value = mock_model_session_manager_instance
        mock_model_session_manager_instance.vocab_path = "fake_vocab.txt"
        mock_model_session_manager_instance.select_sample.return_value = ("ref.wav", "ref text")
        
        engine = TTSEngine()
        text = "xin chao"

        # Act
        with patch.object(engine, 'synthesize', return_value=(np.array([1, 2, 3]), 1.23)):
            result = engine.synthesize(text)

        # Assert
        audio, duration = result
        np.testing.assert_array_equal(audio, np.array([1, 2, 3]))
        self.assertEqual(duration, 1.23)

if __name__ == '__main__':
    unittest.main()
