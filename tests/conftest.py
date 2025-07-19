"""
Pytest configuration and fixtures for VietVoice TTS tests
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import patch
from tests.test_utils import TestFixtures


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_fixtures():
    """Provide test fixtures utility"""
    return TestFixtures()


@pytest.fixture
def mock_model_download():
    """Mock model download to avoid network calls in tests"""
    with patch('vietvoicetts.core.model_config.ModelConfig.ensure_model_downloaded') as mock:
        mock.return_value = "fake_model.pt"
        yield mock


@pytest.fixture
def sample_audio_file(temp_dir, test_fixtures):
    """Provide a sample audio file for testing"""
    file_path = os.path.join(temp_dir, "sample.wav")
    return test_fixtures.create_dummy_audio_file(file_path)


@pytest.fixture
def sample_vocab_file(temp_dir, test_fixtures):
    """Provide a sample vocabulary file for testing"""
    file_path = os.path.join(temp_dir, "vocab.txt")
    return test_fixtures.create_dummy_vocab_file(file_path)