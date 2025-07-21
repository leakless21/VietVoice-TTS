
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from vietvoicetts.client import TTSApi

class TestApi(unittest.TestCase):
    @patch('vietvoicetts.client.TTSEngine')
    def test_synthesize_to_file(self, mock_tts_engine):
        # Arrange
        mock_engine_instance = MagicMock()
        mock_engine_instance.synthesize.return_value = (np.array([1, 2, 3]), 1.23)
        mock_tts_engine.return_value = mock_engine_instance
        api = TTSApi()
        text = "xin chao"
        output_path = "output.wav"

        # Act
        duration = api.synthesize_to_file(text, output_path)

        # Assert
        self.assertEqual(duration, 1.23)
        mock_engine_instance.synthesize.assert_called_once_with(
            text=text,
            gender=None,
            group=None,
            area=None,
            emotion=None,
            output_path=output_path,
            reference_audio=None,
            reference_text=None
        )

if __name__ == '__main__':
    unittest.main()
