"""
Configuration module for Faster Whisper Service
"""
import os
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Model Configuration
    default_model_name: str = Field(
        default="openai/whisper-large-v3",
        description="Default model to load at startup"
    )
    models_base_dir: str = Field(
        default="/data/models",
        description="Base directory for local models"
    )

    # Device Configuration
    device: Literal["cuda", "cpu"] = Field(
        default="cuda",
        description="Device to run inference on"
    )
    compute_type: Literal["float32", "bfloat16", "float16", "int8_float16", "int8"] = Field(
        default="float16",
        description="Compute precision type (float32/bfloat16=best accuracy, int8=fastest)"
    )

    # Performance Configuration
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker threads"
    )
    batch_size: int = Field(
        default=16,
        ge=1,
        le=64,
        description="Batch size for inference"
    )

    # Transcription Settings
    vad_filter: bool = Field(
        default=True,
        description="Enable Voice Activity Detection"
    )
    beam_size: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Beam size for decoding"
    )

    # Audio Processing
    target_sample_rate: int = Field(
        default=16000,
        description="Target sample rate for audio"
    )
    trim_top_db: int = Field(
        default=25,
        description="Top dB for silence trimming"
    )
    normalization_target_db: float = Field(
        default=-23.0,
        description="Target dB for normalization"
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
