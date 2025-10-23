from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from extensions import db
from models import User, FreelancerProfile
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config import SECRET_KEY, JWT_ACCESS_EXPIRES, JWT_REFRESH_EXPIRES
from http import HTTPStatus

# Initialize Flask-RESTX namespace
auth_ns = Namespace('auth', description='Authentication operations')

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
# Define input/output models for Swagger documentation and validation
signup_model = auth_ns.model('Signup', {
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password'),
    'role': fields.String(required=True, enum=['freelancer', 'client'], description='User role')
})
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password')
})
token_response_model = auth_ns.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token')
})