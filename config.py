import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get("SECRET_KEY", "DEFAULT_SECRET")
    
    # Database configuration
    BASE_DIRECTORY = Path(__file__).parent
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIRECTORY}/parking_app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Debug mode
    DEBUG = True
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "my_jwt_secret")
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class DefaultConfig(Config):
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DefaultConfig
}





