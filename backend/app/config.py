import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/qds_siem"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/qds_siem"

    # Security
    SECRET_KEY: str = "qds-siem-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Detection Engine Defaults
    SEVERITY_LOW_MAX: int = 24
    SEVERITY_MEDIUM_MAX: int = 49
    SEVERITY_HIGH_MAX: int = 74
    # 75-100 = Critical

    # Risk Score Weights
    WEIGHT_DEVIATION: float = 0.30
    WEIGHT_VERIFICATION: float = 0.25
    WEIGHT_FREQUENCY: float = 0.15
    WEIGHT_ANOMALY: float = 0.20
    WEIGHT_HASH_MISMATCH: float = 0.10

    # Detection Thresholds
    DEVIATION_THRESHOLD: float = 0.30  # 30%
    ZSCORE_THRESHOLD: float = 2.5
    REPLAY_WINDOW_SECONDS: int = 300  # 5 minutes
    ANOMALY_SENSITIVITY: float = 0.5  # 0-1 scale

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
