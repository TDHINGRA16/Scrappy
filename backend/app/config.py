import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration that works for both Docker and local development
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/scraper_db"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detect if running in Docker and adjust database URL
        if self._is_running_in_docker():
            self.DATABASE_URL = "postgresql+asyncpg://postgres:password@db:5432/scraper_db"
    
    def _is_running_in_docker(self) -> bool:
        """Check if the application is running in a Docker container"""
        # Check for Docker environment indicators
        return (
            os.path.exists('/.dockerenv') or  # Docker creates this file
            os.environ.get('DOCKER_CONTAINER') == 'true' or  # Custom env var
            os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None  # Lambda environment
        )
    
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # SMTP Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True
    
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    SELENIUM_REMOTE_URL: str = "http://selenium:4444/wd/hub"
    
    # Google Sheets Service Account Configuration
    GOOGLE_SERVICE_ACCOUNT_TYPE: str = "service_account"
    GOOGLE_SERVICE_ACCOUNT_PROJECT_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: str = ""
    GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL: str = ""
    GOOGLE_SERVICE_ACCOUNT_CLIENT_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_SERVICE_ACCOUNT_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL: str = ""
    GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN: str = "googleapis.com"
    DEFAULT_GOOGLE_SHEET_ID: str = "1nPIFz7ekgONZqO_b-olnx_NGt05bQHf2UMTdTcswf3A"
    
    # Auth Configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Frontend Configuration
    FRONTEND_URL: str = "https://scrappyy.vercel.app"
    
    # Single User Credentials (for simple auth)
    ADMIN_EMAIL: str = "admin@scrappy.com"
    ADMIN_PASSWORD: str = "change-this-password"

    class Config:
        env_file = ".env"

settings = Settings()
