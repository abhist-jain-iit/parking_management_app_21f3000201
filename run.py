#!/usr/bin/env python3
from app import create_app
import os
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
    try:
        app = create_app('development')
        print("🚀 Starting ParkEase - Vehicle Parking Management System")
        print("📍 Access the application at: http://localhost:5000")
        print("🔑 Admin Login - Username: admin, Password: Admin@123")
        print("=" * 50)
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        exit(1)
