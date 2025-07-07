from functools import wraps
from flask import session, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import *

def require_permission(required_permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_permissions = []
                print('DEBUG: SESSION:', dict(session))
                # Method 1: JWT in Authorization header
                if 'Authorization' in request.headers:
                    try:
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        print('DEBUG: JWT permissions:', user_permissions)
                    except Exception as e:
                        print(f"JWT verification failed: {e}")
                        return jsonify({'msg': 'Invalid token'}), 401
                # Method 2: JWT in session
                elif 'access_token' in session:
                    try:
                        request.environ['HTTP_AUTHORIZATION'] = f'Bearer {session["access_token"]}'
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        print('DEBUG: Session JWT permissions:', user_permissions)
                    except Exception as e:
                        print(f"Session JWT verification failed: {e}")
                        session.pop('access_token', None)
                        return jsonify({'msg': 'Session expired'}), 401
                # Method 3: Session-based admin check
                elif 'user_id' in session:
                    user_id = session.get('user_id')
                    user_role = session.get('user_role', '').lower()
                    print('DEBUG: user_id:', user_id, 'user_role:', user_role)
                    # Admin bypass for specific permissions
                    if user_role == 'admin':
                        admin_permissions = [
                            PermissionType.FULL_SYSTEM_ACCESS.value,
                            PermissionType.MANAGE_USERS.value,
                            PermissionType.MANAGE_PARKING.value,
                            PermissionType.VIEW_ANALYTICS.value,
                            PermissionType.VIEW_PARKING_DETAILS.value,
                            PermissionType.SEARCH_PARKING_SPOTS.value
                        ]
                        user_permissions = admin_permissions
                        print('DEBUG: Admin permissions:', user_permissions)
                    else:
                        # Get user permissions from database
                        user = User.query.get(user_id)
                        if user and hasattr(user, 'user_roles'):
                            for user_role_obj in user.user_roles:
                                if user_role_obj.role and hasattr(user_role_obj.role, 'permissions'):
                                    user_permissions.extend([p.name for p in user_role_obj.role.permissions])
                        print('DEBUG: User permissions:', user_permissions)
                else:
                    print('DEBUG: No authentication found in session or headers')
                    return jsonify({'msg': 'Authentication required'}), 401
                # Check permission
                print('DEBUG: Required permission:', required_permission)
                if required_permission in user_permissions or required_permission in [p for p in user_permissions]:
                    return f(*args, **kwargs)
                else:
                    print('DEBUG: Permission denied. user_permissions:', user_permissions)
                    return jsonify({
                        'msg': f'Permission {required_permission} required',
                        'user_permissions': user_permissions
                    }), 403
            except Exception as e:
                import traceback
                print(f"Permission check error: {e}")
                print(traceback.format_exc())
                print('DEBUG: SESSION ON ERROR:', dict(session))
                return jsonify({'msg': 'Authentication failed', 'error': str(e)}), 401
        return decorated_function
    return decorator