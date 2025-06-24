from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name = 'default'):

    # config_name (str): Which configuration to use ('development', 'production', etc.)

    app = Flask(__name__)
    # Create Flask application instance

    # Load configuration from config.py
    app.config.from_object(config[config_name])

    # Initialize extensions with the app
    db.init_app(app)

    @app.route('/')
    def index():
        return '''
                <h1>🚗 Parking App is Running!</h1>
                <p>Step 1 completed successfully!</p>
                <p>Next: We'll add database models and authentication</p>
            '''
    return app

