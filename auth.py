from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from extensions import jwt
from models import User

# Initialize JWT manager (configured in app.py)
jwt = JWTManager()

# Protect routes with admin role
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt()
        if not current_user or current_user.get('role') != 'admin':
            return {'message': 'Admin access required'}, 403
        return fn(*args, **kwargs)
    return wrapper

# Create JWT token with role claim
def create_token(user):
    additional_claims = {'role': user.role}
    return create_access_token(identity=user.id, additional_claims=additional_claims)