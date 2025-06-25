from flask import Flask , render_template
from config import config
from app.extensions import db


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
        return render_template("home.html")
    return app

