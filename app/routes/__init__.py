from flask import Blueprint

def register_blueprints(app):
    # Register all blueprints with the Flask app

    from .auth import auth_bp
    from .main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    print("✅ All blueprints registered successfully")