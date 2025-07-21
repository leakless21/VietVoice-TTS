"""
Tests for API schemas and validation
"""

import pytest
from pydantic import ValidationError
from vietvoicetts.api.schemas import (
    Gender, Group, Area, Emotion,
    HealthResponse, SynthesizeRequest, SynthesizeFileResponse
)


class TestEnumSchemas:
    """Test enum schema definitions"""

    def test_gender_enum(self):
        """Test Gender enum values"""
        assert Gender.MALE == "male"
        assert Gender.FEMALE == "female"
        
        # Test all values are accessible
        assert len(Gender) == 2
        assert "male" in [g.value for g in Gender]
        assert "female" in [g.value for g in Gender]

    def test_group_enum(self):
        """Test Group enum values"""
        expected_groups = ["story", "news", "audiobook", "interview", "review"]
        actual_groups = [g.value for g in Group]
        
        assert len(Group) == 5
        for group in expected_groups:
            assert group in actual_groups

    def test_area_enum(self):
        """Test Area enum values"""
        expected_areas = ["northern", "southern", "central"]
        actual_areas = [a.value for a in Area]
        
        assert len(Area) == 3
        for area in expected_areas:
            assert area in actual_areas

    def test_emotion_enum(self):
        """Test Emotion enum values"""
        expected_emotions = ["neutral", "serious", "monotone", "sad", "surprised", "happy", "angry"]
        actual_emotions = [e.value for e in Emotion]
        
        assert len(Emotion) == 7
        for emotion in expected_emotions:
            assert emotion in actual_emotions


class TestHealthResponse:
    """Test HealthResponse schema"""

    def test_valid_health_response(self):
        """Test valid health response creation"""
        response = HealthResponse(status="healthy", uptime=123)
        assert response.status == "healthy"
        assert response.uptime == 123

    def test_health_response_serialization(self):
        """Test health response JSON serialization"""
        response = HealthResponse(status="healthy", uptime=456)
        json_data = response.model_dump()
        
        assert json_data == {"status": "healthy", "uptime": 456}

    def test_health_response_from_dict(self):
        """Test creating health response from dictionary"""
        data = {"status": "healthy", "uptime": 789}
        response = HealthResponse(**data)
        
        assert response.status == "healthy"
        assert response.uptime == 789

    def test_invalid_status(self):
        """Test invalid status value"""
        with pytest.raises(ValidationError):
            HealthResponse(status="unhealthy", uptime=123)


class TestSynthesizeRequest:
    """Test SynthesizeRequest schema"""

    def test_minimal_valid_request(self):
        """Test minimal valid synthesis request"""
        request = SynthesizeRequest(text="Hello world")
        
        assert request.text == "Hello world"
        assert request.speed == 0.9  # Default value
        assert request.output_format == "wav"  # Default value
        assert request.gender is None
        assert request.group is None
        assert request.area is None
        assert request.emotion is None

    def test_full_valid_request(self):
        """Test fully specified synthesis request"""
        request = SynthesizeRequest(
            text="Test text",
            speed=1.5,
            output_format="wav",
            gender=Gender.FEMALE,
            group=Group.NEWS,
            area=Area.NORTHERN,
            emotion=Emotion.HAPPY
        )
        
        assert request.text == "Test text"
        assert request.speed == 1.5
        assert request.output_format == "wav"
        assert request.gender == Gender.FEMALE
        assert request.group == Group.NEWS
        assert request.area == Area.NORTHERN
        assert request.emotion == Emotion.HAPPY

    def test_text_validation(self):
        """Test text field validation"""
        # Empty text should fail
        with pytest.raises(ValidationError) as exc_info:
            SynthesizeRequest(text="")
        assert "at least 1 character" in str(exc_info.value)

        # Text too long should fail
        long_text = "a" * 501  # Exceeds max_length of 500
        with pytest.raises(ValidationError) as exc_info:
            SynthesizeRequest(text=long_text)
        assert "at most 500 characters" in str(exc_info.value)

        # Valid text should pass
        request = SynthesizeRequest(text="Valid text")
        assert request.text == "Valid text"

    def test_speed_validation(self):
        """Test speed field validation"""
        # Speed too low should fail
        with pytest.raises(ValidationError) as exc_info:
            SynthesizeRequest(text="Test", speed=0.1)
        assert "greater than or equal to 0.25" in str(exc_info.value)

        # Speed too high should fail
        with pytest.raises(ValidationError) as exc_info:
            SynthesizeRequest(text="Test", speed=2.5)
        assert "less than or equal to 2" in str(exc_info.value)

        # Valid speeds should pass
        request1 = SynthesizeRequest(text="Test", speed=0.25)
        assert request1.speed == 0.25

        request2 = SynthesizeRequest(text="Test", speed=2.0)
        assert request2.speed == 2.0

        request3 = SynthesizeRequest(text="Test", speed=1.0)
        assert request3.speed == 1.0

    def test_output_format_validation(self):
        """Test output format validation"""
        # Valid format
        request = SynthesizeRequest(text="Test", output_format="wav")
        assert request.output_format == "wav"

        # Invalid format should fail
        with pytest.raises(ValidationError):
            SynthesizeRequest(text="Test", output_format="mp3")

    def test_enum_field_validation(self):
        """Test enum field validation"""
        # Valid enum values
        request = SynthesizeRequest(
            text="Test",
            gender=Gender.MALE,
            group=Group.STORY,
            area=Area.SOUTHERN,
            emotion=Emotion.SAD
        )
        assert request.gender == Gender.MALE
        assert request.group == Group.STORY
        assert request.area == Area.SOUTHERN
        assert request.emotion == Emotion.SAD

        # Invalid enum values should fail
        with pytest.raises(ValidationError):
            SynthesizeRequest(text="Test", gender="invalid")

        with pytest.raises(ValidationError):
            SynthesizeRequest(text="Test", group="invalid")

        with pytest.raises(ValidationError):
            SynthesizeRequest(text="Test", area="invalid")

        with pytest.raises(ValidationError):
            SynthesizeRequest(text="Test", emotion="invalid")

    def test_request_serialization(self):
        """Test request serialization to dict"""
        request = SynthesizeRequest(
            text="Test text",
            speed=1.2,
            gender=Gender.FEMALE,
            group=Group.NEWS
        )
        
        data = request.model_dump()
        expected = {
            "text": "Test text",
            "speed": 1.2,
            "output_format": "wav",
            "gender": "female",
            "group": "news",
            "area": None,
            "emotion": None
        }
        assert data == expected

    def test_request_from_dict(self):
        """Test creating request from dictionary"""
        data = {
            "text": "Hello",
            "speed": 1.1,
            "gender": "male",
            "area": "central"
        }
        
        request = SynthesizeRequest(**data)
        assert request.text == "Hello"
        assert request.speed == 1.1
        assert request.gender == Gender.MALE
        assert request.area == Area.CENTRAL
        assert request.group is None  # Not specified
        assert request.emotion is None  # Not specified


class TestSynthesizeFileResponse:
    """Test SynthesizeFileResponse schema"""

    def test_valid_file_response(self):
        """Test valid file response creation"""
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

    def test_file_response_serialization(self):
        """Test file response JSON serialization"""
        response = SynthesizeFileResponse(
            download_url="/download/test",
            duration_seconds=1.23,
            sample_rate=16000,
            format="wav",
            file_size_bytes=512
        )
        
        json_data = response.model_dump()
        expected = {
            "download_url": "/download/test",
            "duration_seconds": 1.23,
            "sample_rate": 16000,
            "format": "wav",
            "file_size_bytes": 512
        }
        assert json_data == expected

    def test_file_response_from_dict(self):
        """Test creating file response from dictionary"""
        data = {
            "download_url": "/api/v1/download/xyz789",
            "duration_seconds": 3.14,
            "sample_rate": 44100,
            "format": "wav",
            "file_size_bytes": 2048
        }
        
        response = SynthesizeFileResponse(**data)
        assert response.download_url == "/api/v1/download/xyz789"
        assert response.duration_seconds == 3.14
        assert response.sample_rate == 44100
        assert response.format == "wav"
        assert response.file_size_bytes == 2048

    def test_required_fields(self):
        """Test that all fields are required"""
        # Missing download_url
        with pytest.raises(ValidationError):
            SynthesizeFileResponse(
                duration_seconds=1.0,
                sample_rate=22050,
                format="wav",
                file_size_bytes=100
            )

        # Missing duration_seconds
        with pytest.raises(ValidationError):
            SynthesizeFileResponse(
                download_url="/download/test",
                sample_rate=22050,
                format="wav",
                file_size_bytes=100
            )

        # Missing sample_rate
        with pytest.raises(ValidationError):
            SynthesizeFileResponse(
                download_url="/download/test",
                duration_seconds=1.0,
                format="wav",
                file_size_bytes=100
            )

        # Missing format
        with pytest.raises(ValidationError):
            SynthesizeFileResponse(
                download_url="/download/test",
                duration_seconds=1.0,
                sample_rate=22050,
                file_size_bytes=100
            )

        # Missing file_size_bytes
        with pytest.raises(ValidationError):
            SynthesizeFileResponse(
                download_url="/download/test",
                duration_seconds=1.0,
                sample_rate=22050,
                format="wav"
            )


class TestSchemaIntegration:
    """Test schema integration and edge cases"""

    def test_enum_string_conversion(self):
        """Test that enum values are properly converted to/from strings"""
        # Create request with string values (as would come from JSON)
        request_data = {
            "text": "Test",
            "gender": "female",
            "group": "audiobook",
            "area": "central",
            "emotion": "surprised"
        }
        
        request = SynthesizeRequest(**request_data)
        
        # Verify enums are properly converted
        assert isinstance(request.gender, Gender)
        assert request.gender == Gender.FEMALE
        assert isinstance(request.group, Group)
        assert request.group == Group.AUDIOBOOK
        assert isinstance(request.area, Area)
        assert request.area == Area.CENTRAL
        assert isinstance(request.emotion, Emotion)
        assert request.emotion == Emotion.SURPRISED

    def test_partial_enum_specification(self):
        """Test requests with only some enum fields specified"""
        request = SynthesizeRequest(
            text="Test",
            gender=Gender.MALE,
            emotion=Emotion.ANGRY
            # group and area not specified
        )
        
        assert request.gender == Gender.MALE
        assert request.emotion == Emotion.ANGRY
        assert request.group is None
        assert request.area is None

    def test_schema_field_descriptions(self):
        """Test that schema fields have proper descriptions"""
        # Check that important fields have descriptions
        schema = SynthesizeRequest.model_json_schema()
        
        assert "description" in schema["properties"]["text"]
        assert "description" in schema["properties"]["speed"]
        assert "description" in schema["properties"]["output_format"]
        
        # Check specific descriptions
        assert "synthesized into speech" in schema["properties"]["text"]["description"]
        assert "speed" in schema["properties"]["speed"]["description"].lower()

    def test_schema_constraints_in_json_schema(self):
        """Test that validation constraints appear in JSON schema"""
        schema = SynthesizeRequest.model_json_schema()
        
        # Text constraints
        text_props = schema["properties"]["text"]
        assert text_props["minLength"] == 1
        assert text_props["maxLength"] == 500
        
        # Speed constraints
        speed_props = schema["properties"]["speed"]
        assert speed_props["minimum"] == 0.25
        assert speed_props["maximum"] == 2.0


if __name__ == "__main__":
    pytest.main([__file__])