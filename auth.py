from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from extensions import jwt
from models import User

# Initialize JWT manager (configured in app.py)
jwt = JWTManager()

# Protect routes with admin role
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            identity = get_jwt_identity()
            user = User.query.get(identity)
            if not user or user.role != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# Create JWT token with role claim
def create_token(user):
    additional_claims = {'role': user.role}
    return create_access_token(identity=user.id, additional_claims=additional_claims)