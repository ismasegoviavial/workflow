from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Workflow Engine Platform"
    ENVIRONMENT: str = "development"
    
    # Base de Datos (Cloud SQL / SQL Server / SQLite para local tests)
    DATABASE_URL: str = "sqlite:///./workflow_engine.db"
    
    # Google Workspace Auth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # GCP Project & Secret Manager
    GCP_PROJECT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
