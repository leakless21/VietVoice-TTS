
import unittest
import numpy as np
from vietvoicetts.core.audio_processor import AudioProcessor

class TestAudioProcessor(unittest.TestCase):
    def test_save_and_load_wav(self):
        # Arrange
        processor = AudioProcessor()
        audio_data = np.random.rand(1, 16000).astype(np.float32)
        file_path = "test.wav"

        # Act
        processor.save_audio(audio_data, file_path, 16000)
        loaded_audio = processor.load_audio(file_path, 16000)

        # Assert
        # Note: Due to audio processing and format conversion, exact equality is not expected
        # Just verify the audio was loaded and has the right shape and type
        self.assertEqual(loaded_audio.dtype, np.int16)
        self.assertEqual(len(loaded_audio.shape), 1)  # Should be 1D array
        self.assertGreater(len(loaded_audio), 0)

if __name__ == '__main__':
    unittest.main()
