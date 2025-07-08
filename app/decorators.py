from functools import wraps
from flask import session, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import *
from flask_login import current_user

def require_permission(required_permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_permissions = []
                debug_info = {}
                # Prefer Flask-Login current_user
                if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                    user = current_user
                    debug_info['current_user'] = user.id
                    if hasattr(user, 'user_roles'):
                        for user_role_obj in user.user_roles:
                            if user_role_obj.role and hasattr(user_role_obj.role, 'role_permissions'):
                                user_permissions.extend([
                                    rp.permission.permission_type.value
                                    for rp in user_role_obj.role.role_permissions
                                ])
                    # Always add SEARCH_PARKING_SPOTS for regular users
                    if PermissionType.SEARCH_PARKING_SPOTS.value not in user_permissions:
                        user_permissions.append(PermissionType.SEARCH_PARKING_SPOTS.value)
                    debug_info['db_permissions'] = user_permissions
                # Fallback: JWT or session
                elif 'Authorization' in request.headers:
                    try:
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        debug_info['jwt_permissions'] = user_permissions
                    except Exception as e:
                        print(f"JWT verification failed: {e}")
                        return jsonify({'msg': 'Invalid token'}), 401
                elif 'access_token' in session:
                    try:
                        request.environ['HTTP_AUTHORIZATION'] = f'Bearer {session["access_token"]}'
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        debug_info['session_jwt_permissions'] = user_permissions
                    except Exception as e:
                        print(f"Session JWT verification failed: {e}")
                        session.pop('access_token', None)
                        return jsonify({'msg': 'Session expired'}), 401
                elif 'user_id' in session:
                    user_id = session.get('user_id')
                    user_role = session.get('user_role', '').lower()
                    debug_info['user_id'] = user_id
                    debug_info['user_role'] = user_role
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
                        debug_info['admin_permissions'] = user_permissions
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
                        debug_info['db_permissions'] = user_permissions
                else:
                    print('DEBUG: No authentication found in session or headers')
                    return jsonify({'msg': 'Authentication required'}), 401
                # Check permission
                print(f'DEBUG: Permission check for {required_permission} | Info: {debug_info}')
                if required_permission in user_permissions or required_permission in [p for p in user_permissions]:
                    return f(*args, **kwargs)
                else:
                    print(f'Permission denied: {required_permission} required. user_permissions: {user_permissions} | Info: {debug_info}')
                    return jsonify({
                        'msg': f'Permission {required_permission} required',
                        'user_permissions': user_permissions,
                        'debug_info': debug_info
                    }), 403
            except Exception as e:
                import traceback
                print(f"Permission check error: {e}")
                print(traceback.format_exc())
                print('DEBUG: SESSION ON ERROR:', dict(session))
                return jsonify({'msg': 'Authentication failed', 'error': str(e)}), 401
        return decorated_function
    return decorator