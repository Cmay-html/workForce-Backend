from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from src.extensions import db
from src.models import User, FreelancerProfile
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from http import HTTPStatus
# from utils.validators import is_valid_role  # Commented out as utils doesn't exist
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_ns = Namespace('auth', description='Authentication operations')

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

@auth_ns.route('/signup')
class Signup(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.marshal_with(token_response_model, code=HTTPStatus.CREATED)
    def post(self):
        """Register a new user (freelancer or client)"""
        data = request.get_json()
        logger.info(f"Signup attempt for email: {data['email']}")

        # Validate email uniqueness
        if User.query.filter_by(email=data['email']).first():
            logger.error(f"Email {data['email']} already exists")
            return {'message': 'Email already exists'}, HTTPStatus.BAD_REQUEST

        # Validate role
        # if not is_valid_role(data['role']):  # Commented out as validator doesn't exist
        if data['role'] not in ['freelancer', 'client']:
            logger.error(f"Invalid role: {data['role']}")
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

        # Create FreelancerProfile for freelancers
        if data['role'] == 'freelancer':
            freelancer_profile = FreelancerProfile(
                user_id=user.id,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(freelancer_profile)
            db.session.commit()
            logger.info(f"FreelancerProfile created for user_id: {user.id}")

        # Generate JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        logger.info(f"User {user.id} signed up successfully")
        return {'access_token': access_token, 'refresh_token': refresh_token}, HTTPStatus.CREATED

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model)
    def post(self):
        """Authenticate a user and return JWT tokens"""
        data = request.get_json()
        logger.info(f"Login attempt for email: {data['email']}")

        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            logger.error(f"Invalid credentials for email: {data['email']}")
            return {'message': 'Invalid email or password'}, HTTPStatus.UNAUTHORIZED

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        logger.info(f"User {user.id} logged in successfully")
        return {'access_token': access_token, 'refresh_token': refresh_token}, HTTPStatus.OK

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.marshal_with(token_response_model)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh an access token using a refresh token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        logger.info(f"Access token refreshed for user {current_user_id}")
        return {'access_token': access_token, 'refresh_token': None}, HTTPStatus.OK

@auth_ns.route('/me')
class UserProfile(Resource):
    @auth_ns.marshal_with(auth_ns.model('User', {
        'id': fields.Integer,
        'email': fields.String,
        'role': fields.String,
        'created_at': fields.DateTime
    }))
    @jwt_required()
    def get(self):
        """Get the authenticated user's profile"""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        logger.info(f"Profile retrieved for user {user_id}")
        return user, HTTPStatus.OK