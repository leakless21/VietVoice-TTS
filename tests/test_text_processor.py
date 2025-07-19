
import unittest
from unittest.mock import patch, mock_open
import numpy as np
from vietvoicetts.core.text_processor import TextProcessor

class TestTextProcessor(unittest.TestCase):
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_text_to_sequence(self, mock_exists):
        # Arrange
        processor = TextProcessor("fake_vocab.txt")
        text = [["a", "b", "c"]]
        
        # Act
        sequence = processor.text_to_indices(text)

        # Assert
        self.assertIsInstance(sequence, np.ndarray)
        self.assertGreater(len(sequence), 0)

if __name__ == '__main__':
    unittest.main()
