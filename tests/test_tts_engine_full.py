
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from vietvoicetts.core.tts_engine import TTSEngine
from vietvoicetts.core.model_config import ModelConfig

class TestTTSEngineFull(unittest.TestCase):

    @patch('vietvoicetts.core.tts_engine.ModelSessionManager')
    @patch('vietvoicetts.core.tts_engine.TextProcessor')
    @patch('vietvoicetts.core.tts_engine.AudioProcessor')
    def setUp(self, mock_audio_processor, mock_text_processor, mock_model_session_manager):
        self.mock_model_session_manager = mock_model_session_manager
        self.mock_text_processor = mock_text_processor
        self.mock_audio_processor = mock_audio_processor
        
        # Mock instances
        self.mock_model_session_manager.return_value.vocab_path = 'fake_vocab.txt'
        self.mock_text_processor_instance = self.mock_text_processor.return_value
        self.mock_audio_processor_instance = self.mock_audio_processor.return_value
        
        self.config = ModelConfig()
        self.engine = TTSEngine(self.config)

    def test_init(self):
        self.mock_model_session_manager.assert_called_once_with(self.config)
        self.mock_model_session_manager.return_value.load_models.assert_called_once()
        self.mock_text_processor.assert_called_once_with('fake_vocab.txt')
        self.mock_audio_processor.assert_called_once()

    def test_prepare_inputs_single_chunk(self):
        self.mock_audio_processor_instance.load_audio.return_value = np.zeros((1, 16000))
        self.mock_text_processor_instance.clean_text.side_effect = lambda x: x
        self.mock_text_processor_instance.calculate_text_length.return_value = 10
        self.mock_text_processor_instance.text_to_indices.return_value = np.array([[1,2,3]])

        inputs_list = self.engine._prepare_inputs('ref.wav', 'ref text', 'target text')
        
        self.assertEqual(len(inputs_list), 1)
        self.assertEqual(len(inputs_list[0]), 4)

    def test_prepare_inputs_multiple_chunks(self):
        self.mock_audio_processor_instance.load_audio.return_value = np.zeros((1, 24000 * 5)) # 5 seconds audio
        self.mock_text_processor_instance.clean_text.side_effect = lambda x: x
        # ref_text, target_text, chunk1_post, chunk2_post, chunk1_final, chunk2_final
        self.mock_text_processor_instance.calculate_text_length.side_effect = [50, 500, 40, 40, 40, 40]
        self.mock_text_processor_instance.chunk_text.return_value = ['a long chunk', 'another long chunk']
        self.mock_text_processor_instance.text_to_indices.return_value = np.array([[1,2,3]])

        inputs_list = self.engine._prepare_inputs('ref.wav', 'ref text', 'a very long target text that should be chunked')
        
        self.assertEqual(len(inputs_list), 2)

    @patch.object(TTSEngine, '_run_preprocess')
    @patch.object(TTSEngine, '_run_transformer_steps')
    @patch.object(TTSEngine, '_run_decode')
    def test_synthesize(self, mock_decode, mock_transformer, mock_preprocess):
        self.engine._prepare_inputs = MagicMock(return_value=[
            (np.zeros(1), np.zeros(1), np.zeros(1), np.zeros(1))
        ])
        mock_preprocess.return_value = [np.zeros(1)] * 8
        mock_transformer.return_value = (np.zeros(1), np.zeros(1))
        mock_decode.return_value = np.zeros((1, 16000))
        self.mock_model_session_manager.return_value.select_sample.return_value = ('ref.wav', 'ref text')
        self.mock_audio_processor_instance.concatenate_with_crossfade_improved.return_value = np.zeros((1, 16000))

        audio, duration = self.engine.synthesize('text')

        self.assertIsInstance(audio, np.ndarray)
        self.assertIsInstance(duration, float)
        self.engine._prepare_inputs.assert_called_once()
        mock_preprocess.assert_called_once()
        mock_transformer.assert_called_once()
        mock_decode.assert_called_once()

if __name__ == '__main__':
    unittest.main()
