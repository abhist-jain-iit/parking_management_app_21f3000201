from app import create_app
# from app.extensions import db
# from app.models.user import User, Role

# Route for testing database....

# @app.route('/test-db')
# def test_database():
#     try:
#         # Counts
#         user_count = User.query.count()
#         role_count = Role.query.count()

#         admin = User.query.filter_by(user_name='admin').first()

#         # User and Admin check.

#         return f"Users: {user_count}, Roles: {role_count}, Admin Exists: {'Yes' if admin else 'No'}"

#     except Exception as e: # For the case if the default User and Admin are not created.
#         print(f"Error creating app: {e}")
#         return "Database test failed", 500

if __name__ == "__main__":
    app = create_app('development')
    app.run(debug=True, host="0.0.0.0", port=5000)
