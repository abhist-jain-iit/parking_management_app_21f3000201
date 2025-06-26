from flask import Flask , render_template
from config import config
from app.extensions import db
from app.routes import register_blueprints  
from app.models.database_setup import init_database

def create_app(config_name = 'default'):

    # config_name (str): Which configuration to use ('development', 'production', etc.)

    app = Flask(__name__)
    # Create Flask application instance

    # Load configuration from config.py
    app.config.from_object(config[config_name])

    # Initialize extensions with the app
    db.init_app(app)
    
    # This route was for out main page but now we have created main.py inside routes folder. So we gonna use that now.

    init_database(app)  # Initialize the database with default data
    # @app.route('/')
    # def index():
    #     return render_template("home.html")


    # Register blueprints
    register_blueprints(app)

    return app

