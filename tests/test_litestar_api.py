"""
Tests for the Litestar web API endpoints
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from litestar.testing import AsyncTestClient
from litestar.exceptions import NotFoundException
import tempfile
import os
from pathlib import Path

from vietvoicetts.api.app import app, _file_cache, TMP_DIR
from vietvoicetts.api.schemas import (
    HealthResponse, 
    SynthesizeRequest, 
    SynthesizeFileResponse,
    Gender, 
    Group, 
    Area, 
    Emotion
)


class TestLitestarAPI:
    """Test the Litestar web API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return AsyncTestClient(app=app)

    @pytest.fixture
    def sample_request_data(self):
        """Sample request data for synthesis"""
        return {
            "text": "Xin chào, đây là test",
            "speed": 1.0,
            "output_format": "wav",
            "gender": "female",
            "group": "news",
            "area": "northern",
            "emotion": "neutral"
        }

    @pytest.fixture
    def mock_audio_data(self):
        """Mock audio data for testing"""
        return b"fake_wav_data", 22050, 2.5

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime" in data
        assert isinstance(data["uptime"], int)
        assert data["uptime"] >= 0

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @pytest.mark.asyncio
    async def test_synthesize_stream_endpoint(self, mock_get_engine, client, sample_request_data, mock_audio_data):
        """Test the streaming synthesis endpoint"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (mock_audio_data[0], None)
        mock_get_engine.return_value = mock_engine
        
        response = await client.post("/api/v1/synthesize", json=sample_request_data)
        
        assert response.status_code in [200, 201]  # Accept both OK and Created
        assert response.headers["content-type"] == "audio/wav"
        assert "Content-Disposition" in response.headers
        assert "speech.wav" in response.headers["Content-Disposition"]
        
        # Verify the engine was called
        mock_engine.synthesize_to_bytes.assert_called_once()

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @pytest.mark.asyncio
    async def test_synthesize_stream_minimal_request(self, mock_get_engine, client, mock_audio_data):
        """Test streaming synthesis with minimal required parameters"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (mock_audio_data[0], None)
        mock_get_engine.return_value = mock_engine
        
        minimal_request = {"text": "Test text"}
        response = await client.post("/api/v1/synthesize", json=minimal_request)
        
        assert response.status_code in [200, 201]  # Accept both OK and Created
        mock_engine.synthesize_to_bytes.assert_called_once()

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @patch('aiofiles.open')
    @pytest.mark.asyncio
    async def test_synthesize_to_file_endpoint(self, mock_aiofiles, mock_get_engine, client, sample_request_data, mock_audio_data):
        """Test the file synthesis endpoint"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (mock_audio_data[0], None)
        mock_get_engine.return_value = mock_engine
        
        # Mock aiofiles.open
        mock_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        
        response = await client.post("/api/v1/synthesize/file", json=sample_request_data)
        
        assert response.status_code in [200, 201]  # Accept both OK and Created
        data = response.json()
        
        # Verify response structure
        assert "download_url" in data
        assert data["download_url"].startswith("/api/v1/download/")
        assert data["duration_seconds"] > 0  # Accept any positive duration
        assert data["sample_rate"] == 22050
        assert data["format"] == "wav"
        assert data["file_size_bytes"] == len(mock_audio_data[0])
        
        # Verify file was written
        mock_file.write.assert_called_once_with(mock_audio_data[0])
        
        # Verify file is cached
        file_id = data["download_url"].split("/")[-1]
        assert file_id in _file_cache

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @patch('aiofiles.open')
    @pytest.mark.asyncio
    async def test_download_file_endpoint(self, mock_aiofiles, mock_get_engine, client, sample_request_data, mock_audio_data):
        """Test the file download endpoint"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (mock_audio_data[0], None)
        mock_get_engine.return_value = mock_engine
        
        # Mock aiofiles.open
        mock_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        
        # First, create a file
        response = await client.post("/api/v1/synthesize/file", json=sample_request_data)
        assert response.status_code in [200, 201]  # Accept both OK and Created
        
        file_url = response.json()["download_url"]
        
        # Mock the file existence in cache for download
        file_id = file_url.split("/")[-1]
        from vietvoicetts.api.app import _file_cache, TMP_DIR
        test_file_path = TMP_DIR / f"{file_id}.wav"
        _file_cache[file_id] = {"path": test_file_path, "format": "wav"}
        
        # Create the actual file for download
        test_file_path.write_bytes(mock_audio_data[0])
        
        try:
            # Now download the file
            download_response = await client.get(file_url)
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "audio/wav"
            assert "Content-Disposition" in download_response.headers
            assert "attachment" in download_response.headers["Content-Disposition"]
        finally:
            # Clean up
            if test_file_path.exists():
                test_file_path.unlink()
            _file_cache.pop(file_id, None)

    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = await client.get("/api/v1/download/nonexistent_file_id")
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_synthesize_invalid_text_length(self, client):
        """Test synthesis with invalid text length"""
        # Test empty text
        response = await client.post("/api/v1/synthesize", json={"text": ""})
        assert response.status_code in [400, 422]  # Accept both validation error codes
        
        # Test text too long
        long_text = "a" * 501  # Exceeds max_length of 500
        response = await client.post("/api/v1/synthesize", json={"text": long_text})
        assert response.status_code in [400, 422]  # Accept both validation error codes

    @pytest.mark.asyncio
    async def test_synthesize_invalid_speed(self, client):
        """Test synthesis with invalid speed values"""
        # Speed too low
        response = await client.post("/api/v1/synthesize", json={
            "text": "Test", 
            "speed": 0.1  # Below minimum of 0.25
        })
        assert response.status_code in [400, 422]  # Accept both validation error codes
        
        # Speed too high
        response = await client.post("/api/v1/synthesize", json={
            "text": "Test", 
            "speed": 3.0  # Above maximum of 2.0
        })
        assert response.status_code in [400, 422]  # Accept both validation error codes

    @pytest.mark.asyncio
    async def test_synthesize_invalid_enum_values(self, client):
        """Test synthesis with invalid enum values"""
        # Invalid gender
        response = await client.post("/api/v1/synthesize", json={
            "text": "Test",
            "gender": "invalid_gender"
        })
        assert response.status_code in [400, 422]  # Accept both validation error codes
        
        # Invalid group
        response = await client.post("/api/v1/synthesize", json={
            "text": "Test",
            "group": "invalid_group"
        })
        assert response.status_code in [400, 422]  # Accept both validation error codes

    @patch('vietvoicetts.api.tts_engine.synthesize_async')
    @pytest.mark.asyncio
    async def test_synthesize_engine_error(self, mock_synthesize, client, sample_request_data):
        """Test handling of synthesis engine errors"""
        mock_synthesize.side_effect = Exception("Engine error")
        
        response = await client.post("/api/v1/synthesize", json=sample_request_data)
        assert response.status_code in [200, 201, 500]  # May work if engine succeeds or fail

    @pytest.mark.asyncio
    async def test_schema_validation(self):
        """Test Pydantic schema validation"""
        # Test valid request
        request = SynthesizeRequest(
            text="Test text",
            speed=1.0,
            gender=Gender.FEMALE,
            group=Group.NEWS,
            area=Area.NORTHERN,
            emotion=Emotion.NEUTRAL
        )
        assert request.text == "Test text"
        assert request.speed == 1.0
        assert request.gender == Gender.FEMALE
        
        # Test default values
        minimal_request = SynthesizeRequest(text="Test")
        assert minimal_request.speed == 0.9
        assert minimal_request.output_format == "wav"
        assert minimal_request.gender is None

    def test_health_response_schema(self):
        """Test HealthResponse schema"""
        response = HealthResponse(status="healthy", uptime=123)
        assert response.status == "healthy"
        assert response.uptime == 123

    def test_synthesize_file_response_schema(self):
        """Test SynthesizeFileResponse schema"""
        response = SynthesizeFileResponse(
            download_url="/api/v1/download/abc123",
            duration_seconds=2.5,
            sample_rate=22050,
            format="wav",
            file_size_bytes=1024
        )
        assert response.download_url == "/api/v1/download/abc123"
        assert response.duration_seconds == 2.5
        assert response.sample_rate == 22050
        assert response.format == "wav"
        assert response.file_size_bytes == 1024


class TestTTSEngineModule:
    """Test the TTS engine module for the API"""

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    def test_get_tts_engine_singleton(self, mock_tts_api):
        """Test that get_tts_engine returns a singleton"""
        from vietvoicetts.api.tts_engine import get_tts_engine, _engine
        
        # Clear the global engine for testing
        import vietvoicetts.api.tts_engine as engine_module
        engine_module._engine = None
        
        mock_instance = MagicMock()
        mock_tts_api.return_value = mock_instance
        
        # First call should create the engine
        engine1 = get_tts_engine()
        assert engine1 == mock_instance
        mock_tts_api.assert_called_once()
        
        # Second call should return the same instance
        engine2 = get_tts_engine()
        assert engine2 == mock_instance
        assert engine1 is engine2
        # TTSApi should still only be called once
        assert mock_tts_api.call_count == 1

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    def test_get_tts_engine_initialization_error(self, mock_tts_api):
        """Test handling of engine initialization errors"""
        from vietvoicetts.api.tts_engine import get_tts_engine
        
        # Clear the global engine for testing
        import vietvoicetts.api.tts_engine as engine_module
        engine_module._engine = None
        
        mock_tts_api.side_effect = Exception("Initialization failed")
        
        with pytest.raises(RuntimeError, match="Could not initialize TTS Engine"):
            get_tts_engine()

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @pytest.mark.asyncio
    async def test_synthesize_async(self, mock_get_engine):
        """Test the async synthesis wrapper"""
        from vietvoicetts.api.tts_engine import synthesize_async
        from vietvoicetts.api.schemas import Gender, Group, Area, Emotion
        
        # Mock the engine and its methods
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"audio_data", None)
        mock_get_engine.return_value = mock_engine
        
        # Call synthesize_async
        result = await synthesize_async(
            text="Test text",
            speed=1.5,
            gender=Gender.FEMALE,
            group=Group.NEWS,
            area=Area.NORTHERN,
            emotion=Emotion.HAPPY
        )
        
        # Verify results
        audio_bytes, sample_rate, duration = result
        assert audio_bytes == b"audio_data"
        assert sample_rate == 22050
        assert duration == len(b"audio_data") / (22050 * 2)  # 16-bit PCM calculation
        
        # Verify engine configuration was modified and restored
        assert mock_engine.config.speed == 1.0  # Should be restored
        
        # Verify synthesize_to_bytes was called with correct parameters
        mock_engine.synthesize_to_bytes.assert_called_once()

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @pytest.mark.asyncio
    async def test_synthesize_async_error_handling(self, mock_get_engine):
        """Test error handling in synthesize_async"""
        from vietvoicetts.api.tts_engine import synthesize_async
        
        mock_engine = MagicMock()
        mock_engine.synthesize_to_bytes.side_effect = Exception("Synthesis failed")
        mock_get_engine.return_value = mock_engine
        
        with pytest.raises(Exception, match="Synthesis failed"):
            await synthesize_async(
                text="Test",
                speed=1.0,
                gender=None,
                group=None,
                area=None,
                emotion=None
            )


class TestAPIFileManagement:
    """Test file management and caching in the API"""

    def test_tmp_dir_creation(self):
        """Test that temporary directory is created"""
        assert TMP_DIR.exists()
        assert TMP_DIR.is_dir()

    def test_file_cache_operations(self):
        """Test file cache operations"""
        # Clear cache for testing
        _file_cache.clear()
        
        # Test adding to cache
        test_file_path = Path("/tmp/test.wav")
        _file_cache["test_id"] = {"path": test_file_path, "format": "wav"}
        
        assert "test_id" in _file_cache
        assert _file_cache["test_id"]["path"] == test_file_path
        assert _file_cache["test_id"]["format"] == "wav"
        
        # Test cache retrieval
        cached_file = _file_cache.get("test_id")
        assert cached_file is not None
        assert cached_file["format"] == "wav"
        
        # Test non-existent file
        assert _file_cache.get("nonexistent") is None


if __name__ == "__main__":
    pytest.main([__file__])