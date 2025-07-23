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

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_respects_word_boundaries(self, mock_exists):
        """Test that chunk_text respects word boundaries when splitting long text."""
        processor = TextProcessor("fake_vocab.txt")
        
        # Test case 1: Long text that needs splitting at word boundaries
        long_text = "This is a very long sentence that should be split at word boundaries instead of character boundaries to ensure natural speech."
        chunks = processor.chunk_text(long_text, max_chars=50)
        
        # Verify no chunks exceed max_chars
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 50, f"Chunk exceeds max_chars: {chunk}")
        
        # Verify words are not split (ignore punctuation and trailing periods)
        import string
        def normalize(word):
            return word.strip(string.punctuation)
        original_words = set(normalize(w) for w in long_text.split())
        for chunk in chunks:
            chunk_words = chunk.split()
            for word in chunk_words:
                clean_word = normalize(word)
                if clean_word:
                    self.assertIn(clean_word, original_words, f"Word '{clean_word}' was split incorrectly")
        
        # Test case 2: Single very long word
        long_word = "Supercalifragilisticexpialidocious"
        chunks = processor.chunk_text(long_word, max_chars=20)
        # Should return the word as-is since it's a single word
        self.assertEqual(chunks, [long_word])

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_vietnamese_text(self, mock_exists):
        """Test chunking with Vietnamese text."""
        processor = TextProcessor("fake_vocab.txt")
        
        vietnamese_text = "Xin chào các bạn, đây là một đoạn văn bản tiếng Việt cần được chia nhỏ một cách hợp lý để đảm bảo chất lượng giọng nói tự nhiên."
        chunks = processor.chunk_text(vietnamese_text, max_chars=40)
        
        # Verify no chunks exceed max_chars
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 40, f"Chunk exceeds max_chars: {chunk}")
        
        # Verify Vietnamese words are preserved (ignore punctuation and trailing periods)
        import string
        def normalize(word):
            return word.strip(string.punctuation)
        original_words = set(normalize(w) for w in vietnamese_text.split())
        for chunk in chunks:
            chunk_words = chunk.split()
            for word in chunk_words:
                clean_word = normalize(word)
                if clean_word:
                    self.assertIn(clean_word, original_words, f"Vietnamese word '{clean_word}' was split incorrectly")

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_short_text(self, mock_exists):
        """Test that short text is returned as single chunk."""
        processor = TextProcessor("fake_vocab.txt")
        
        short_text = "Hello world"
        chunks = processor.chunk_text(short_text, max_chars=50)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_empty_string(self, mock_exists):
        """Test handling of empty string."""
        processor = TextProcessor("fake_vocab.txt")
        
        chunks = processor.chunk_text("", max_chars=50)
        self.assertEqual(chunks, [])

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_whitespace_only(self, mock_exists):
        """Test handling of whitespace-only string."""
        processor = TextProcessor("fake_vocab.txt")
        
        chunks = processor.chunk_text("   \n\t  ", max_chars=50)
        self.assertEqual(chunks, [])

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_maintains_soft_constraint(self, mock_exists):
        """Test that max_chars is a soft constraint - never exceeded unless single word is longer."""
        processor = TextProcessor("fake_vocab.txt")
        
        # Test with text that has words of varying lengths
        text = "The quick brown fox jumps over the lazy dog. This is a test sentence for chunking purposes."
        chunks = processor.chunk_text(text, max_chars=30)
        
        # Verify no chunk exceeds max_chars (except possibly single long words)
        for chunk in chunks:
            words = chunk.split()
            if len(words) > 1:
                self.assertLessEqual(len(chunk), 30, f"Multi-word chunk exceeds max_chars: {chunk}")

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="a\nb\nc\n"))
    def test_chunk_text_edge_case_single_long_word(self, mock_exists):
        """Test edge case where a single word exceeds max_chars."""
        processor = TextProcessor("fake_vocab.txt")
        
        long_word = "Pneumonoultramicroscopicsilicovolcanoconiosis"
        chunks = processor.chunk_text(long_word, max_chars=20)
        
        # Single long word should be returned as-is
        self.assertEqual(chunks, [long_word])
        self.assertGreater(len(chunks[0]), 20)


if __name__ == '__main__':
    unittest.main()
