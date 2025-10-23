# utils/auth.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models.user import User

def role_required(roles):
    """Middleware to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                current_user = User.query.get(current_user_id)
                
                if not current_user:
                    return jsonify({
                        'success': False,
                        'message': 'User not found'
                    }), 404
                
                if current_user.role not in roles:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient permissions'
                    }), 403
                    
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Authentication failed'
                }), 401
        return decorated_function
    return decorator

# Role-specific decorators
def client_required(f):
    """Require client role"""
    return role_required(['client'])(f)

def freelancer_required(f):
    """Require freelancer role"""
    return role_required(['freelancer'])(f)

def admin_required(f):
    """Require admin role"""
    return role_required(['admin'])(f)

def get_current_user():
    """Get current user from JWT"""
    try:
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except:
        return None