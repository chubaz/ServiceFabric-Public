from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fabric API Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    FLASK_SERVICE_URL: str = "http://flask_base:5000"
    DJANGO_SERVICE_URL: str = "http://backend_api:8000"
    class Config:
        case_sensitive = True

settings = Settings()
