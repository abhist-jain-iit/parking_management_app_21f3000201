from flask import Flask
from config import config
from app.extensions import db, login_manager
from app.routes import register_blueprints  
from app.models.database_setup import init_database
from flask_jwt_extended import JWTManager

def create_app(config_name='default'):
    """Create and configure Ease-Park! Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize database with default data
    init_database(app)
    
    # User loader for Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    register_blueprints(app)
    
    return app


