from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from extensions import jwt
from models import User

# Initialize JWT manager (configured in app.py)
jwt = JWTManager()

# Custom claim to include user role
@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    user = User.query.get(identity)
    if user:
        return {'role': user.role}
    return {'role': 'guest'}

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

# Create JWT token
def create_token(user):
    additional_claims = {'role': user.role}
    return create_access_token(identity=user.id, additional_claims=additional_claims)