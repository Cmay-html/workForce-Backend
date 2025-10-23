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

# Apply CORS to the Flask app (move to main app.py if needed)
# CORS(app)  # Uncomment if this is the main app file; otherwise, ensure it's in app.py

@auth_ns.route('/signup')
class Signup(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.marshal_with(token_response_model, code=HTTPStatus.CREATED)
    @limiter.limit("10 per minute")  # Limit signup attempts to prevent abuse
    def post(self):
        """Register a new user (freelancer or client)"""
        data = request.get_json()

        # Validate email uniqueness
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already exists'}, HTTPStatus.BAD_REQUEST

        # Validate role
        if data['role'] not in ['freelancer', 'client']:
            return {'message': 'Invalid role. Must be freelancer or client'}, HTTPStatus.BAD_REQUEST

        # Create new user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data['role'],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(user)
        db.session.commit()
        # If role is freelancer, create a FreelancerProfile
        if data['role'] == 'freelancer':
            freelancer_profile = FreelancerProfile(
                user_id=user.id,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(freelancer_profile)
            db.session.commit()

        # Generate JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {'access_token': access_token, 'refresh_token': refresh_token}, HTTPStatus.CREATED