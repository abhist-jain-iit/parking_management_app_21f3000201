from functools import wraps
from flask import session, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models import *
from flask_login import current_user

def require_permission(required_permission):
    """Decorator to check user permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_permissions = []
                
                # Check Flask-Login current_user first
                if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    user = current_user
                    if hasattr(user, 'user_roles'):
                        for user_role_obj in user.user_roles:
                            if user_role_obj.role and hasattr(user_role_obj.role, 'role_permissions'):
                                user_permissions.extend([
                                    rp.permission.permission_type.value
                                    for rp in user_role_obj.role.role_permissions
                                ])
                    # Add search permission for regular users
                    if PermissionType.SEARCH_PARKING_SPOTS.value not in user_permissions:
                        user_permissions.append(PermissionType.SEARCH_PARKING_SPOTS.value)
                
                # Fallback to JWT authentication
                elif 'Authorization' in request.headers:
                    try:
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                    except Exception:
                        return jsonify({'msg': 'Invalid token'}), 401
                
                # Fallback to session authentication
                elif 'user_id' in session:
                    user_id = session.get('user_id')
                    user_role = session.get('user_role', '').lower()
                    
                    if user_role == 'admin':
                        user_permissions = [
                            PermissionType.FULL_SYSTEM_ACCESS.value,
                            PermissionType.MANAGE_USERS.value,
                            PermissionType.MANAGE_PARKING.value,
                            PermissionType.VIEW_ANALYTICS.value,
                            PermissionType.VIEW_PARKING_DETAILS.value,
                            PermissionType.SEARCH_PARKING_SPOTS.value
                        ]
                    else:
                        user = User.query.get(user_id)
                        if user and hasattr(user, 'user_roles'):
                            for user_role_obj in user.user_roles:
                                if user_role_obj.role and hasattr(user_role_obj.role, 'role_permissions'):
                                    user_permissions.extend([
                                        rp.permission.permission_type.value
                                        for rp in user_role_obj.role.role_permissions
                                    ])
                        if PermissionType.SEARCH_PARKING_SPOTS.value not in user_permissions:
                            user_permissions.append(PermissionType.SEARCH_PARKING_SPOTS.value)
                else:
                    return jsonify({'msg': 'Authentication required'}), 401
                
                # Check if user has required permission
                if required_permission in user_permissions:
                    return f(*args, **kwargs)
                else:
                    return jsonify({'msg': f'Permission {required_permission} required'}), 403
                    
            except Exception as e:
                return jsonify({'msg': 'Authentication failed'}), 401
                
        return decorated_function
    return decorator