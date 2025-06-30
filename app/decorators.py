from functools import wraps
from flask import session, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import *

def require_permission(required_permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Method 1: Check if JWT token is in Authorization header
                if 'Authorization' in request.headers:
                    verify_jwt_in_request()
                    claims = get_jwt()
                    user_permissions = claims.get('permissions', [])
                    
                    if required_permission in user_permissions:
                        return f(*args, **kwargs)
                    else:
                        return jsonify({'msg': f'Permission {required_permission} required'}), 403
                
                # Method 2: Check if JWT token is in session (for web interface)
                elif 'access_token' in session:
                    # Temporarily add the token to headers for verification
                    from werkzeug.datastructures import EnvironHeaders
                    
                    # Create a new headers object with the Authorization header
                    new_headers = dict(request.headers)
                    new_headers['Authorization'] = f'Bearer {session["access_token"]}'
                    
                    # Replace request headers temporarily
                    original_headers = request.headers
                    request.headers = EnvironHeaders(new_headers)
                    
                    try:
                        verify_jwt_in_request()
                        claims = get_jwt()
                        user_permissions = claims.get('permissions', [])
                        
                        if required_permission in user_permissions:
                            return f(*args, **kwargs)
                        else:
                            return jsonify({'msg': f'Permission {required_permission} required'}), 403
                    finally:
                        # Restore original headers
                        request.headers = original_headers
                
                # Method 3: Fallback to session-based check for admin
                elif 'user_id' in session and session.get('user_role') == 'admin':
                    # Admin users get access to specific permissions
                    admin_allowed_permissions = [
                        PermissionType.FULL_SYSTEM_ACCESS.value,
                        PermissionType.MANAGE_USERS.value
                        # Add other admin permissions as needed
                    ]
                    
                    if required_permission in admin_allowed_permissions:
                        return f(*args, **kwargs)
                    else:
                        return jsonify({'msg': f'Permission {required_permission} required'}), 403
                
                else:
                    return jsonify({'msg': 'Authentication required'}), 401
                    
            except Exception as e:
                print(f"Permission check error: {e}")
                return jsonify({'msg': 'Authentication failed'}), 401
        
        return decorated_function
    return decorator