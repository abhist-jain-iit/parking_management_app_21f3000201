import os
from pathlib import Path

class Config:
    # Contains settings that are common across all environments.

    # On windows use "set SECRET_KEY = ABHIST_JAIN" to set our secret key if no .env file is there.
    SECRET_KEY = os.environ.get("SECRET_KEY", "default_dev_secret")

    # Now Database Configuration
    # Here lets find out the Base Path first.
    # Then database file will be created in the project root.
    BASE_DIR = Path(__file__).parent # This gives the directory that contains the file.

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR}/parking_app.db"

    # Disable SQLAlchemy event system to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

class DevelopmentConfig(Config):
    # Inherits from base Config class
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development' : DevelopmentConfig,
    'production' : ProductionConfig,
    'default' : DevelopmentConfig
}





