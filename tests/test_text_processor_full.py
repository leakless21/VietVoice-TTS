

import unittest
from unittest.mock import patch, mock_open
import numpy as np
from vietvoicetts.core.text_processor import TextProcessor

class TestTextProcessorFull(unittest.TestCase):

    def setUp(self):
        self.vocab_content = "a\nb\nc\n"
        self.m = mock_open(read_data=self.vocab_content)

    @patch("pathlib.Path.exists", return_value=True)
    def test_load_vocab(self, mock_exists):
        with patch("builtins.open", self.m):
            processor = TextProcessor("fake_vocab.txt")
            self.assertEqual(processor.vocab_char_map, {'a': 0, 'b': 1, 'c': 2})

    @patch("pathlib.Path.exists", return_value=True)
    def test_text_to_indices(self, mock_exists):
        with patch("builtins.open", self.m):
            processor = TextProcessor("fake_vocab.txt")
            indices = processor.text_to_indices([['a', 'b', 'c']])
            np.testing.assert_array_equal(indices, np.array([[0, 1, 2]]))

    def test_calculate_text_length(self):
        processor = TextProcessor.__new__(TextProcessor) # No init
        length = processor.calculate_text_length("a, b, c.", r"[,.]")
        self.assertEqual(length, len("a, b, c.".encode('utf-8')) + 3 * 3)

    def test_clean_text(self):
        processor = TextProcessor.__new__(TextProcessor) # No init
        cleaned = processor.clean_text("  a;b:c(d)   efg! ")
        self.assertEqual(cleaned, "a,b,c,d, efg!")

    def test_chunk_text(self):
        processor = TextProcessor.__new__(TextProcessor) # No init
        text = "This is a long sentence. This is another long sentence. And a third one."
        chunks = processor.chunk_text(text, max_chars=30)
        self.assertTrue(all(len(c) <= 30 for c in chunks))
        self.assertEqual(len(chunks), 4)

if __name__ == '__main__':
    unittest.main()


