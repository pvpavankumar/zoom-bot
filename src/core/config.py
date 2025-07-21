
import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

print("0000000000000")

class Settings(BaseSettings):
    print("completed p1")

    environment: str = Field(default="development", env="NODE_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    print("1111111111111")

    host: str = Field(default="localhost", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    print("completed p2")

    zoom_api_key: str = Field(..., env="ZOOM_API_KEY")
    zoom_api_secret: str = Field(..., env="ZOOM_API_SECRET")
    zoom_webhook_secret: str = Field(..., env="ZOOM_WEBHOOK_SECRET")
    zoom_sdk_key: str = Field(..., env="ZOOM_SDK_KEY")
    zoom_sdk_secret: str = Field(..., env="ZOOM_SDK_SECRET")
    print("2222222222222")

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_org_id: Optional[str] = Field(default=None, env="OPENAI_ORG_ID")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    print("completed p3")

    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    enable_audio_processing: bool = Field(default=True, env="ENABLE_AUDIO_PROCESSING")
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    audio_chunk_size: int = Field(default=1024, env="AUDIO_CHUNK_SIZE")
    audio_format: str = Field(default="wav", env="AUDIO_FORMAT")

    run_startup_tests: bool = Field(default=True, env="RUN_STARTUP_TESTS")
    skip_tests_on_failure: bool = Field(default=True, env="SKIP_TESTS_ON_FAILURE")
    speech_recognition_timeout: int = Field(default=5, env="SPEECH_RECOGNITION_TIMEOUT")
    voice_activity_detection_threshold: float = Field(default=0.6, env="VOICE_ACTIVITY_DETECTION_THRESHOLD")

    audio_buffer_duration: float = Field(default=3.0, env="AUDIO_BUFFER_DURATION")
    min_speech_duration: float = Field(default=0.5, env="MIN_SPEECH_DURATION")
    max_silence_duration: float = Field(default=2.0, env="MAX_SILENCE_DURATION")
    speech_end_timeout: float = Field(default=1.5, env="SPEECH_END_TIMEOUT")

    bot_name: str = Field(default="InterviewBot", env="BOT_NAME")
    bot_display_name: str = Field(default="AI Interview Assistant", env="BOT_DISPLAY_NAME")
    bot_hidden_mode: bool = Field(default=True, env="BOT_HIDDEN_MODE")
    max_concurrent_rooms: int = Field(default=10, env="MAX_CONCURRENT_ROOMS")
    suggestion_frequency: int = Field(default=30, env="SUGGESTION_FREQUENCY")
    context_window_size: int = Field(default=1000, env="CONTEXT_WINDOW_SIZE")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/zoom_bot.log", env="LOG_FILE")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    prometheus_port: int = Field(default=8001, env="PROMETHEUS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("audio_format")
    @classmethod
    def validate_audio_format(cls, v):
        valid_formats = ["wav", "mp3", "flac", "m4a"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Audio format must be one of: {valid_formats}")
        return v.lower()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


settings = Settings()


def get_settings() -> Settings:
    return settings


def is_development() -> bool:
    return settings.environment == "development"


def is_production() -> bool:
    return settings.environment == "production"


def create_log_directory():
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
