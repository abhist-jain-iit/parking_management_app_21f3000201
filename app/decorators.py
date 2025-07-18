from functools import wraps
from flask import session, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models import *
from flask_login import current_user
from app.models.enums import PermissionType

def require_permission(required_permission):
    """Decorator to check user permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_permissions = []
                debug_info = {}
                # Check Flask-Login current_user first
                if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    user = current_user
                    debug_info['auth_branch'] = 'flask_login'
                    debug_info['username'] = getattr(user, 'username', None)
                    # Always grant all permissions to the admin user
                    if hasattr(user, 'username') and user.username == 'admin':
                        user_permissions = [p.value for p in PermissionType]
                        debug_info['permissions'] = user_permissions
                    elif hasattr(user, 'user_roles'):
                        for user_role_obj in user.user_roles:
                            if user_role_obj.role and hasattr(user_role_obj.role, 'role_permissions'):
                                user_permissions.extend([
                                    rp.permission.permission_type.value
                                    for rp in user_role_obj.role.role_permissions
                                ])
                        debug_info['permissions'] = user_permissions
                    # Add search permission for regular users
                    if PermissionType.SEARCH_PARKING_SPOTS.value not in user_permissions:
                        user_permissions.append(PermissionType.SEARCH_PARKING_SPOTS.value)
                # Fallback to JWT authentication
                elif 'Authorization' in request.headers:
                    debug_info['auth_branch'] = 'jwt'
                    try:
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        debug_info['permissions'] = user_permissions
                    except Exception:
                        print('[DEBUG require_permission] JWT branch:', debug_info)
                        return jsonify({'msg': 'Invalid token'}), 401
                # Fallback to session authentication
                elif 'user_id' in session:
                    debug_info['auth_branch'] = 'session'
                    user_id = session.get('user_id')
                    user_role = session.get('user_role', '').lower()
                    debug_info['user_id'] = user_id
                    debug_info['user_role'] = user_role
                    if user_role == 'admin':
                        user_permissions = [
                            PermissionType.FULL_SYSTEM_ACCESS.value,
                            PermissionType.MANAGE_USERS.value,
                            PermissionType.MANAGE_PARKING.value,
                            PermissionType.VIEW_ANALYTICS.value,
                            PermissionType.VIEW_PARKING_DETAILS.value,
                            PermissionType.SEARCH_PARKING_SPOTS.value
                        ]
                        debug_info['permissions'] = user_permissions
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
                        debug_info['permissions'] = user_permissions
                else:
                    print('[DEBUG require_permission] No authentication branch matched:', debug_info)
                    return jsonify({'msg': 'Authentication required'}), 401
                print('[DEBUG require_permission] branch:', debug_info)
                # Check if user has required permission
                if required_permission in user_permissions:
                    return f(*args, **kwargs)
                else:
                    print('[DEBUG require_permission] Permission denied:', required_permission, debug_info)
                    return jsonify({'msg': f'Permission {required_permission} required'}), 403
            except Exception as e:
                print('[DEBUG require_permission] Exception:', str(e))
                return jsonify({'msg': 'Authentication failed'}), 401
        return decorated_function
    return decorator