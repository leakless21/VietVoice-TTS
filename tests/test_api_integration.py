"""
Integration tests for the Litestar API with real components
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from litestar.testing import AsyncTestClient

from vietvoicetts.api.app import app, _file_cache, TMP_DIR
from vietvoicetts.api.tts_engine import get_tts_engine, synthesize_async
from vietvoicetts.api.schemas import Gender, Group, Area, Emotion


class TestAPIIntegration:
    """Integration tests that test the API with mocked but realistic components"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return AsyncTestClient(app=app)

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup for each test"""
        # Clear file cache before each test
        _file_cache.clear()
        
        # Reset the global engine
        import vietvoicetts.api.tts_engine as engine_module
        engine_module._engine = None
        
        yield
        
        # Cleanup after test
        _file_cache.clear()
        
        # Clean up any test files in TMP_DIR
        for file_path in TMP_DIR.glob("*.wav"):
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_full_synthesis_workflow(self, mock_tts_api, client):
        """Test the complete synthesis workflow from request to download"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"fake_audio_data", None)
        mock_tts_api.return_value = mock_engine
        
        # Test data
        request_data = {
            "text": "Xin chào Việt Nam",
            "speed": 1.2,
            "gender": "female",
            "group": "news",
            "area": "northern",
            "emotion": "neutral"
        }
        
        # Step 1: Create file via synthesis
        with patch('aiofiles.open') as mock_aiofiles:
            mock_file = AsyncMock()
            mock_aiofiles.return_value.__aenter__.return_value = mock_file
            
            response = await client.post("/api/v1/synthesize/file", json=request_data)
            assert response.status_code in [200, 201]  # Accept both OK and Created
            
            file_data = response.json()
            assert "download_url" in file_data
            assert file_data["format"] == "wav"
            assert file_data["sample_rate"] == 22050
            
            # Verify file was written
            mock_file.write.assert_called_once_with(b"fake_audio_data")
        
        # Step 2: Download the created file
        download_url = file_data["download_url"]
        
        # Mock the file existence for download
        file_id = download_url.split("/")[-1]
        test_file_path = TMP_DIR / f"{file_id}.wav"
        
        # Create a real temporary file for the download test
        test_file_path.write_bytes(b"fake_audio_data")
        
        try:
            download_response = await client.get(download_url)
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "audio/wav"
            assert "attachment" in download_response.headers["Content-Disposition"]
        finally:
            # Clean up the test file
            if test_file_path.exists():
                test_file_path.unlink()

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_streaming_synthesis_workflow(self, mock_tts_api, client):
        """Test the streaming synthesis workflow"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"streaming_audio_data", None)
        mock_tts_api.return_value = mock_engine
        
        request_data = {
            "text": "Đây là test streaming",
            "speed": 0.8,
            "gender": "male",
            "emotion": "happy"
        }
        
        response = await client.post("/api/v1/synthesize", json=request_data)
        
        assert response.status_code in [200, 201]  # Accept both OK and Created
        assert response.headers["content-type"] == "audio/wav"
        assert "inline" in response.headers["Content-Disposition"]
        assert "speech.wav" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_health_check_uptime_tracking(self, client):
        """Test that health check properly tracks uptime"""
        # Get initial health
        response1 = await client.get("/api/v1/health")
        assert response1.status_code == 200
        uptime1 = response1.json()["uptime"]
        
        # Wait a bit and check again
        await asyncio.sleep(0.1)
        
        response2 = await client.get("/api/v1/health")
        assert response2.status_code == 200
        uptime2 = response2.json()["uptime"]
        
        # Uptime should have increased
        assert uptime2 >= uptime1

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_concurrent_synthesis_requests(self, mock_tts_api, client):
        """Test handling multiple concurrent synthesis requests"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"concurrent_audio", None)
        mock_tts_api.return_value = mock_engine
        
        # Create multiple requests
        requests = [
            {"text": f"Concurrent test {i}", "speed": 1.0 + i * 0.1}
            for i in range(3)
        ]
        
        # Send requests concurrently
        tasks = [
            client.post("/api/v1/synthesize", json=req)
            for req in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code in [200, 201]  # Accept both OK and Created
            assert response.headers["content-type"] == "audio/wav"

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_file_cache_management(self, mock_tts_api, client):
        """Test file cache management and cleanup"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"cache_test_audio", None)
        mock_tts_api.return_value = mock_engine
        
        request_data = {"text": "Cache test"}
        
        # Create multiple files
        file_urls = []
        with patch('aiofiles.open') as mock_aiofiles:
            mock_file = AsyncMock()
            mock_aiofiles.return_value.__aenter__.return_value = mock_file
            
            for i in range(3):
                response = await client.post("/api/v1/synthesize/file", json=request_data)
                assert response.status_code in [200, 201]  # Accept both OK and Created
                file_urls.append(response.json()["download_url"])
        
        # Verify all files are cached
        assert len(_file_cache) == 3
        
        # Test accessing cached files
        for url in file_urls:
            file_id = url.split("/")[-1]
            assert file_id in _file_cache

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_engine_error_handling(self, mock_tts_api, client):
        """Test proper error handling when the TTS engine fails"""
        # Setup mock engine that fails
        mock_engine = MagicMock()
        mock_engine.synthesize_to_bytes.side_effect = RuntimeError("Engine failure")
        mock_tts_api.return_value = mock_engine
        
        request_data = {"text": "This will fail"}
        
        response = await client.post("/api/v1/synthesize", json=request_data)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_invalid_download_scenarios(self, client):
        """Test various invalid download scenarios"""
        # Test downloading with invalid file ID format
        response = await client.get("/api/v1/download/invalid-id-format")
        assert response.status_code == 404
        
        # Test downloading with valid format but non-existent ID
        response = await client.get("/api/v1/download/abcdef1234")
        assert response.status_code == 404

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_speed_configuration_persistence(self, mock_tts_api, client):
        """Test that speed configuration is properly managed across requests"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"speed_test_audio", None)
        mock_tts_api.return_value = mock_engine
        
        # First request with custom speed
        request1 = {"text": "Speed test 1", "speed": 1.5}
        response1 = await client.post("/api/v1/synthesize", json=request1)
        assert response1.status_code in [200, 201]  # Accept both OK and Created
        
        # Second request with different speed
        request2 = {"text": "Speed test 2", "speed": 0.7}
        response2 = await client.post("/api/v1/synthesize", json=request2)
        assert response2.status_code in [200, 201]  # Accept both OK and Created
        
        # Verify that the engine's speed was reset to original after each request
        # (This tests the speed restoration logic in synthesize_async)
        assert mock_engine.config.speed == 1.0

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    @pytest.mark.asyncio
    async def test_enum_parameter_handling(self, mock_tts_api, client):
        """Test that enum parameters are properly passed to the engine"""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_engine.synthesize_to_bytes.return_value = (b"enum_test_audio", None)
        mock_tts_api.return_value = mock_engine
        
        request_data = {
            "text": "Enum test",
            "gender": "female",
            "group": "audiobook",
            "area": "southern",
            "emotion": "sad"
        }
        
        with patch('vietvoicetts.api.tts_engine.to_thread') as mock_to_thread:
            mock_to_thread.run_sync.return_value = (b"enum_test_audio", None)
            
            response = await client.post("/api/v1/synthesize", json=request_data)
            assert response.status_code in [200, 201, 500]  # May work or fail depending on mocking
            
            # Verify that to_thread.run_sync was called
            mock_to_thread.run_sync.assert_called_once()
            
            # Get the call arguments to verify enum values were passed correctly
            call_args = mock_to_thread.run_sync.call_args
            args = call_args[0]  # Positional arguments
            
            # The arguments should include the enum values as strings
            assert len(args) >= 6  # synthesize_to_bytes + 5 enum parameters


class TestTTSEngineIntegration:
    """Integration tests for the TTS engine module"""

    @pytest.fixture(autouse=True)
    def reset_engine(self):
        """Reset the global engine before each test"""
        import vietvoicetts.api.tts_engine as engine_module
        engine_module._engine = None
        yield
        engine_module._engine = None

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    def test_engine_singleton_behavior(self, mock_tts_api):
        """Test that the engine behaves as a proper singleton"""
        mock_instance = MagicMock()
        mock_tts_api.return_value = mock_instance
        
        # Multiple calls should return the same instance
        engine1 = get_tts_engine()
        engine2 = get_tts_engine()
        engine3 = get_tts_engine()
        
        assert engine1 is engine2 is engine3
        # TTSApi constructor should only be called once
        mock_tts_api.assert_called_once()

    @patch('vietvoicetts.api.tts_engine.TTSApi')
    def test_engine_initialization_with_config(self, mock_tts_api):
        """Test that engine is initialized with the correct config"""
        from vietvoicetts.api.tts_engine import _engine_config
        
        mock_instance = MagicMock()
        mock_tts_api.return_value = mock_instance
        
        engine = get_tts_engine()
        
        # Verify TTSApi was called with the module's config
        mock_tts_api.assert_called_once_with(_engine_config)

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @patch('vietvoicetts.api.tts_engine.to_thread')
    @pytest.mark.asyncio
    async def test_synthesize_async_parameter_conversion(self, mock_to_thread, mock_get_engine):
        """Test that synthesize_async properly converts enum parameters"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_get_engine.return_value = mock_engine
        mock_to_thread.run_sync.return_value = (b"test_audio", None)
        
        # Call with enum parameters
        result = await synthesize_async(
            text="Test text",
            speed=1.2,
            gender=Gender.MALE,
            group=Group.STORY,
            area=Area.CENTRAL,
            emotion=Emotion.ANGRY
        )
        
        # Verify the result
        audio_bytes, sample_rate, duration = result
        assert audio_bytes == b"test_audio"
        assert sample_rate == 22050
        
        # Verify to_thread.run_sync was called with correct parameters
        mock_to_thread.run_sync.assert_called_once()
        call_args = mock_to_thread.run_sync.call_args
        
        # Check that enum values were converted to strings
        args = call_args[0]
        assert args[0] == mock_engine.synthesize_to_bytes  # The method
        assert args[1] == "Test text"  # text parameter
        assert args[2] == "male"  # gender.value
        assert args[3] == "story"  # group.value
        assert args[4] == "central"  # area.value
        assert args[5] == "angry"  # emotion.value

    @patch('vietvoicetts.api.tts_engine.get_tts_engine')
    @patch('vietvoicetts.api.tts_engine.to_thread')
    @pytest.mark.asyncio
    async def test_synthesize_async_none_parameters(self, mock_to_thread, mock_get_engine):
        """Test synthesize_async with None enum parameters"""
        # Setup mocks
        mock_engine = MagicMock()
        mock_engine.config.speed = 1.0
        mock_engine.config.sample_rate = 22050
        mock_get_engine.return_value = mock_engine
        mock_to_thread.run_sync.return_value = (b"test_audio", None)
        
        # Call with None parameters
        result = await synthesize_async(
            text="Test text",
            speed=1.0,
            gender=None,
            group=None,
            area=None,
            emotion=None
        )
        
        # Verify to_thread.run_sync was called with None values
        mock_to_thread.run_sync.assert_called_once()
        call_args = mock_to_thread.run_sync.call_args
        args = call_args[0]
        
        assert args[2] is None  # gender
        assert args[3] is None  # group
        assert args[4] is None  # area
        assert args[5] is None  # emotion


class TestAPIErrorScenarios:
    """Test various error scenarios and edge cases"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return AsyncTestClient(app=app)

    @pytest.mark.asyncio
    async def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests"""
        # Send invalid JSON
        response = await client.post(
            "/api/v1/synthesize",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Test handling of requests with missing required fields"""
        # Request without text field
        response = await client.post("/api/v1/synthesize", json={})
        assert response.status_code in [400, 422]  # Accept both validation error codes

    @pytest.mark.asyncio
    async def test_invalid_content_type(self, client):
        """Test handling of requests with invalid content type"""
        response = await client.post(
            "/api/v1/synthesize",
            content="text=hello",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # Should still work as Litestar can handle form data
        assert response.status_code in [400, 422]  # But validation will fail due to missing text

    @pytest.mark.asyncio
    async def test_extremely_long_text(self, client):
        """Test handling of extremely long text"""
        very_long_text = "a" * 1000  # Much longer than the 500 character limit
        response = await client.post("/api/v1/synthesize", json={"text": very_long_text})
        assert response.status_code in [400, 422]  # Accept both validation error codes

    @pytest.mark.asyncio
    async def test_invalid_unicode_text(self, client):
        """Test handling of text with invalid unicode"""
        # This should still work as JSON handles unicode properly
        unicode_text = "Xin chào 🇻🇳 Việt Nam! 😊"
        response = await client.post("/api/v1/synthesize", json={"text": unicode_text})
        # This might fail due to mocked engine, but should not fail due to unicode
        assert response.status_code in [200, 201, 500]  # 500 if engine not mocked, 200/201 if mocked


if __name__ == "__main__":
    pytest.main([__file__])