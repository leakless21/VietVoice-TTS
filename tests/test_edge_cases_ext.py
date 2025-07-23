import pytest
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

from vietvoicetts.client import TTSApi
from vietvoicetts.core.text_processor import TextProcessor

class TestEdgeCasesExt(unittest.TestCase):
    @patch('vietvoicetts.client.TTSEngine')
    def test_long_non_repeating_text(self, mock_engine):
        """Test handling of long, non-repeating text"""
        api = TTSApi()
        long_text = "Trăm năm trong cõi người ta, chữ tài chữ mệnh khéo là ghét nhau. Trải qua một cuộc bể dâu, những điều trông thấy mà đau đớn lòng. Lạ gì bỉ sắc tư phong, trời xanh quen thói má hồng đánh ghen."
        with patch.object(api.engine, 'synthesize') as mock_synthesize:
            mock_synthesize.return_value = (np.array([0.1, 0.2]), 1.0)
            result = api.synthesize(long_text)
            self.assertIsNotNone(result)

    def test_text_with_different_styles(self):
        """Test handling of text with different speaking styles"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data="a\nb\nc\n")):
                processor = TextProcessor("fake_vocab.txt")
                
                # Formal style
                formal_text = "Kính thưa quý vị, hôm nay chúng ta sẽ thảo luận về một vấn đề quan trọng."
                cleaned_formal = processor.clean_text(formal_text)
                self.assertIsInstance(cleaned_formal, str)
                
                # Informal style
                informal_text = "Ê, bồ! Đi đâu đó? Lâu rồi không gặp."
                cleaned_informal = processor.clean_text(informal_text)
                self.assertIsInstance(cleaned_informal, str)

    def test_text_with_emotional_tones(self):
        """Test handling of text with different emotional tones"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data="a\nb\nc\n")):
                processor = TextProcessor("fake_vocab.txt")
                
                # Happy tone
                happy_text = "Ôi, tuyệt vời! Tôi rất vui khi nghe tin này."
                cleaned_happy = processor.clean_text(happy_text)
                self.assertIsInstance(cleaned_happy, str)
                
                # Sad tone
                sad_text = "Buồn quá... Tôi không biết phải làm sao nữa."
                cleaned_sad = processor.clean_text(sad_text)
                self.assertIsInstance(cleaned_sad, str)
                
                # Angry tone
                angry_text = "Thật không thể chấp nhận được! Tại sao lại như vậy?"
                cleaned_angry = processor.clean_text(angry_text)
                self.assertIsInstance(cleaned_angry, str)

if __name__ == '__main__':
    unittest.main()
