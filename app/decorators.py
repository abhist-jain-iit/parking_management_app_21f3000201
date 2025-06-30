from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import *
from app.extensions import db

def require_permission(required_permission):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user:
                return jsonify({'error': 'User not found'}), 401

            # Check if the user has the required permission via roles
            has_permission = db.session.query(Permission).join(
                RolePermission, RolePermission.permission_id == Permission.id
            ).join(
                UserRole, UserRole.role_id == RolePermission.role_id
            ).filter(
                UserRole.user_id == user.id,
                Permission.permission_type == required_permission
            ).first()

            if not has_permission:
                return jsonify({'error': 'Access denied'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
