
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import argparse
from vietvoicetts.cli import main, create_config, run_interactive_mode
from vietvoicetts.core.model_config import ModelConfig

class TestCliFull(unittest.TestCase):

    @patch('vietvoicetts.cli.TTSApi')
    def test_main_non_interactive_mode(self, mock_tts_api):
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_file.return_value = 1.23  # Return a float
        mock_tts_api.return_value = mock_api_instance
        
        sys.argv = [
            'vietvoice-tts',
            'xin chào',
            'output.wav',
            '--gender', 'female',
            '--area', 'northern',
            '--speed', '1.2',
            '--random-seed', '12345'
        ]
        
        main()
        
        mock_tts_api.assert_called_once()
        mock_api_instance.synthesize_to_file.assert_called_once_with(
            text='xin chào',
            output_path='output.wav',
            gender='female',
            group=None,
            area='northern',
            emotion=None,
            reference_audio=None,
            reference_text=None
        )

    def test_create_config_from_args(self):
        args = argparse.Namespace(
            model_url=None,
            nfe_step=32,
            fuse_nfe=1,
            speed=1.2,
            random_seed=12345,
            cross_fade_duration=0.1,
            max_chunk_duration=15.0,
            min_target_duration=1.0,
            inter_op_threads=0,
            intra_op_threads=0,
            log_severity=4
        )
        config = create_config(args)
        self.assertIsInstance(config, ModelConfig)
        self.assertEqual(config.speed, 1.2)
        self.assertEqual(config.random_seed, 12345)

    def test_create_config_from_dict(self):
        settings = {
            'speed': 1.5,
            'random_seed': 54321,
            'nfe_step': 64
        }
        config = create_config(settings)
        self.assertIsInstance(config, ModelConfig)
        self.assertEqual(config.speed, 1.5)
        self.assertEqual(config.random_seed, 54321)
        self.assertEqual(config.nfe_step, 64)

    @patch('builtins.input', side_effect=['test text', 'test_output', '7', 'yes'])
    @patch('vietvoicetts.cli.TTSApi')
    def test_run_interactive_mode_synthesize(self, mock_tts_api, mock_input):
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_file.return_value = 1.23
        mock_tts_api.return_value = mock_api_instance
        
        run_interactive_mode()
        
        mock_tts_api.assert_called_once()
        mock_api_instance.synthesize_to_file.assert_called_once()
        
    @patch('builtins.input', side_effect=['test text', 'test_output', '1', '1', '1', '1', '1', '7', 'yes'])
    @patch('vietvoicetts.cli.TTSApi')
    def test_run_interactive_mode_edit_voice(self, mock_tts_api, mock_input):
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_file.return_value = 1.23
        mock_tts_api.return_value = mock_api_instance
        
        run_interactive_mode()
        
        # Check that gender selection was called (the exact prompt may vary based on current state)
        gender_calls = [call for call in mock_input.call_args_list if 'current: ' in str(call) and 'option [0-2]' in str(call)]
        self.assertTrue(len(gender_calls) > 0, f"Expected gender selection call not found in: {mock_input.call_args_list}")

    @patch('vietvoicetts.cli.main')
    def test_cli_entry_point(self, mock_main):
        with patch.object(sys, 'argv', ['vietvoice-tts', 'hello', 'out.wav']):
            from vietvoicetts.__main__ import main as entry_main
            entry_main()
            mock_main.assert_called_once()

if __name__ == '__main__':
    unittest.main()
