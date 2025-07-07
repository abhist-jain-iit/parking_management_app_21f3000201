from flask import Blueprint

def register_blueprints(app):
    # Register all blueprints with the Flask app

    from .main import main_bp # Route for Landing Page.
    from .auth import auth_bp # for authentication related routes.
    from .admin import admin_bp, user_geo_bp
    from .user import user_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp , url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(user_geo_bp, url_prefix='/user-geo')

    print("All blueprints registered successfully")



#        Routes so far we have are:

#        / -> main page.
#        /auth/login -> for login.
#        /auth/signup -> for signup page.
#        /auth/logout -> for logout.
#        /auth/admin/login -> admin login.
#        /auth/forgot-password -> Forgot Password.
#        /auth/reset-password/<token> -> Reset-Password
#        /auth/change-password -> Change Password
#        
# 
# 
#        /admin/dashboard -> For Admin Dashboard
#        /admin/users -> Manage Users.
#        /admin/users/<int:user_id>
#        /admin/users/<int:user_id>/edit -> For editing.
#        /admin/users/<int:user_id>/delete -> For deleting Users.
#        /admin/users/<int:user_id>/status -> Status.
#        /admin/lots ->Lots
#        /admin/lots/create
#        /admin/lots/<int:lot_id>
#        /admin/lots/<int:lot_id>/edit
#        /admin/lots/<int:lot_id>/delete
#        /admin/parking/lots/search


#        /admin/spots 
#        /admin/spots/<int:spot_id>
#        /admin/spots/<int:spot_id>/edit
#        /admin/spots/<int:spot_id>/delete

#        /admin/parking/spots/search
#        /admin/parking/spots/<int:spot_id>/update-status

#        /admin/geography
#        /admin/geography/create
#        /admin/geography/<entity>/<int:entity_id>/edit
#        /admin/geography/<entity>/<int:entity_id>/delete
#        /user-geo/create -> Create New Geography
#        /admin/charts
