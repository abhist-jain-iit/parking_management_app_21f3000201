import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Contains settings that are common across all environments.

    # On windows we can use "set SECRET_KEY = ABHIST_JAIN" to set our secret key if no .env file is there.
    SECRET_KEY = os.environ.get("SECRET_KEY", "DEFAULT_SECRET")

    # Now Database Configuration
    # Here lets find out the Base Path first.
    # Then database file will be created in the project root.
    BASE_DIRECTORY = Path(__file__).parent # This gives the directory that contains the file.

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIRECTORY}/parking_app.db"

    # Disable SQLAlchemy event system to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

    # JWT Config
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "my_jwt_secret")
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'


class DevelopmentConfig(Config):
    # Inherits from base Config class
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class DefaultConfig(Config):
    # Default configuration, can be used if no specific environment is set.
    DEBUG = True

config = {
    'development' : DevelopmentConfig,
    'production' : ProductionConfig,
    'default' : DefaultConfig
}





