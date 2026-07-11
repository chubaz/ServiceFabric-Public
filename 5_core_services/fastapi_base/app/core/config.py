from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings


DEVELOPMENT_JWT_SECRET = "servicefabric-development-jwt-secret-not-for-production"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fabric API Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    FLASK_SERVICE_URL: str = "http://flask_base:5000"
    DJANGO_SERVICE_URL: str = "http://backend_api:8000"

    FABRIC_ENVIRONMENT: str = "development"
    JWT_SECRET_KEY: str = DEVELOPMENT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "servicefabric-development"
    JWT_AUDIENCE: str = "servicefabric-fastapi-development"
    JWT_TOKEN_TYPE: str = "fabric_internal"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    MAX_REQUEST_BODY_BYTES: int = 1_048_576
    MAX_VECTOR_DOCUMENTS: int = 100
    MAX_VECTOR_DOCUMENT_CHARS: int = 20_000
    MAX_VECTOR_METADATA_BYTES: int = 8_192
    MAX_VECTOR_TOP_K: int = 25

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.FABRIC_ENVIRONMENT.lower() != "production":
            return self

        if (
            self.JWT_SECRET_KEY == DEVELOPMENT_JWT_SECRET
            or len(self.JWT_SECRET_KEY) < 32
            or self.JWT_SECRET_KEY.startswith("replace_")
        ):
            raise ValueError("JWT_SECRET_KEY must be explicitly configured with a secure value in production")
        if not self.JWT_ISSUER or self.JWT_ISSUER == "servicefabric-development":
            raise ValueError("JWT_ISSUER must be explicitly configured in production")
        if not self.JWT_AUDIENCE or self.JWT_AUDIENCE == "servicefabric-fastapi-development":
            raise ValueError("JWT_AUDIENCE must be explicitly configured in production")
        if not self.cors_allowed_origins or "*" in self.cors_allowed_origins:
            raise ValueError("production CORS_ALLOWED_ORIGINS must contain explicit origins")
        return self

    class Config:
        case_sensitive = True


settings = Settings()
