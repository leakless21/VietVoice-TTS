# vietvoicetts/api/schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class Gender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"

class Group(str, Enum):
    """Voice group/style options."""
    STORY = "story"
    NEWS = "news"
    AUDIOBOOK = "audiobook"
    INTERVIEW = "interview"
    REVIEW = "review"

class Area(str, Enum):
    """Voice regional accent options."""
    NORTHERN = "northern"
    SOUTHERN = "southern"
    CENTRAL = "central"

class Emotion(str, Enum):
    """Voice emotion options."""
    NEUTRAL = "neutral"
    SERIOUS = "serious"
    MONOTONE = "monotone"
    SAD = "sad"
    SURPRISED = "surprised"
    HAPPY = "happy"
    ANGRY = "angry"

class HealthResponse(BaseModel):
    """The response for the health check endpoint."""
    status: Literal["healthy"]
    uptime: int = Field(..., description="Uptime of the server in seconds.")

class SynthesizeRequest(BaseModel):
    """The request body for speech synthesis."""
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="The text to be synthesized into speech."
    )
    speed: float = Field(
        0.9, 
        ge=0.25, 
        le=2.0, 
        description="Speech speed. 0.9 is normal speed."
    )
    output_format: Literal["wav"] = Field(
        "wav", 
        description="The output audio format."
    )
    gender: Optional[Gender] = Field(
        None, description="Filter voice by gender."
    )
    group: Optional[Group] = Field(
        None, description="Filter voice by group/style."
    )
    area: Optional[Area] = Field(
        None, description="Filter voice by regional accent."
    )
    emotion: Optional[Emotion] = Field(
        None, description="Filter voice by emotion."
    )
    sample_iteration: Optional[int] = Field(
        None, 
        ge=0, 
        description="Choose which iteration of available samples to use (0-based index). If not specified, the first available sample is used."
    )

class SynthesizeFileResponse(BaseModel):
    """The response when requesting synthesis to a file."""
    download_url: str = Field(..., description="The URL to download the generated audio file.")
    duration_seconds: float = Field(..., description="The duration of the audio in seconds.")
    sample_rate: int = Field(..., description="The sample rate of the audio in Hz.")
    format: str = Field(..., description="The audio format.")
    file_size_bytes: int = Field(..., description="The size of the audio file in bytes.")