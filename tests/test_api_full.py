
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from vietvoicetts.api import TTSApi, synthesize, synthesize_to_bytes
from vietvoicetts.core.model_config import ModelConfig

class TestApiFull(unittest.TestCase):

    @patch('vietvoicetts.api.TTSEngine')
    def test_tts_api_init_with_config(self, mock_tts_engine):
        config = ModelConfig(speed=1.5)
        api = TTSApi(config)
        self.assertIs(api.config, config)
        self.assertIsNone(api._engine)

    @patch('vietvoicetts.api.TTSEngine')
    def test_tts_api_init_no_config(self, mock_tts_engine):
        api = TTSApi()
        self.assertIsInstance(api.config, ModelConfig)

    @patch('vietvoicetts.api.TTSEngine')
    def test_tts_api_engine_property(self, mock_tts_engine):
        api = TTSApi()
        engine = api.engine
        self.assertIs(engine, mock_tts_engine.return_value)
        self.assertIs(api.engine, engine)  # Should return the same instance

    @patch('vietvoicetts.api.TTSEngine')
    def test_synthesize(self, mock_tts_engine):
        mock_engine_instance = MagicMock()
        mock_engine_instance.synthesize.return_value = (np.array([1,2,3]), 1.23)
        mock_tts_engine.return_value = mock_engine_instance
        api = TTSApi()
        audio, duration = api.synthesize('text')
        self.assertEqual(duration, 1.23)
        np.testing.assert_array_equal(audio, np.array([1,2,3]))
        mock_engine_instance.synthesize.assert_called_once_with(
            text='text',
            gender=None,
            group=None,
            area=None,
            emotion=None,
            output_path=None,
            reference_audio=None,
            reference_text=None
        )

    @patch('vietvoicetts.api.TTSApi.synthesize')
    def test_synthesize_to_file(self, mock_synthesize):
        mock_synthesize.return_value = (np.array([1,2,3]), 1.23)
        api = TTSApi()
        duration = api.synthesize_to_file('text', 'output.wav')
        self.assertEqual(duration, 1.23)
        mock_synthesize.assert_called_once()

    @patch('vietvoicetts.api.TTSApi.synthesize_to_file')
    @patch('builtins.open')
    @patch('tempfile.NamedTemporaryFile')
    def test_synthesize_to_bytes(self, mock_tempfile, mock_open, mock_synthesize_to_file):
        mock_synthesize_to_file.return_value = 1.23
        mock_temp_file_instance = MagicMock()
        mock_temp_file_instance.name = 'temp.wav'
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file_instance
        mock_open.return_value.__enter__.return_value.read.return_value = b'wav_data'
        
        api = TTSApi()
        wav_bytes, duration = api.synthesize_to_bytes('text')
        
        self.assertEqual(wav_bytes, b'wav_data')
        self.assertEqual(duration, 1.23)
        mock_synthesize_to_file.assert_called_once()

    @patch('vietvoicetts.api.TTSApi')
    def test_convenience_synthesize(self, mock_tts_api):
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_file.return_value = 1.23
        mock_tts_api.return_value = mock_api_instance
        
        duration = synthesize('text', 'output.wav')
        
        self.assertEqual(duration, 1.23)
        mock_tts_api.assert_called_once()
        mock_api_instance.synthesize_to_file.assert_called_once_with(
            text='text',
            output_path='output.wav',
            gender=None,
            group=None,
            area=None,
            emotion=None,
            reference_audio=None,
            reference_text=None
        )

    @patch('vietvoicetts.api.TTSApi')
    def test_convenience_synthesize_to_bytes(self, mock_tts_api):
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_bytes.return_value = (b'wav_data', 1.23)
        mock_tts_api.return_value = mock_api_instance
        
        wav_bytes, duration = synthesize_to_bytes('text')
        
        self.assertEqual(wav_bytes, b'wav_data')
        self.assertEqual(duration, 1.23)
        mock_tts_api.assert_called_once()
        mock_api_instance.synthesize_to_bytes.assert_called_once_with(
            text='text',
            gender=None,
            group=None,
            area=None,
            emotion=None,
            reference_audio=None,
            reference_text=None
        )

if __name__ == '__main__':
    unittest.main()
