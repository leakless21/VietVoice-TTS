
import unittest
from unittest.mock import patch, MagicMock
import sys
from vietvoicetts.cli import main

class TestCli(unittest.TestCase):
    @patch('vietvoicetts.cli.TTSApi')
    def test_cli_with_args(self, mock_tts_api):
        # Arrange
        mock_api_instance = MagicMock()
        mock_api_instance.synthesize_to_file.return_value = 1.23  # Return a float
        mock_tts_api.return_value = mock_api_instance
        sys.argv = ['vietvoice-tts', 'xin chao', 'output.wav']

        # Act
        main()

        # Assert
        mock_api_instance.synthesize_to_file.assert_called_once()

if __name__ == '__main__':
    unittest.main()
