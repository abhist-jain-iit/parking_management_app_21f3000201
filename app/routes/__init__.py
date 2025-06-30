from flask import Blueprint

def register_blueprints(app):
    # Register all blueprints with the Flask app

    from .main import main_bp # Route for Landing Page.
    from .auth import auth_bp # for authentication related routes.
    from .admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp , url_prefix='/admin')

    print("✅ All blueprints registered successfully")



#        Routes so far we have are:

#        / -> main page.
#        /auth/login -> for login.
#        /auth/signup -> for signup page.

#        /logout -> for logout.