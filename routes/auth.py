from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, FreelancerProfile
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from http import HTTPStatus
# from utils.validators import is_valid_role  # Commented out as utils doesn't exist
import logging
import secrets
# from utils.email_service import EmailService  # Commented out - email verification removed
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

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

google_login_model = auth_ns.model('GoogleLogin', {
    'credential': fields.String(required=True, description='Google ID Token'),
    'role': fields.String(required=False, enum=['freelancer', 'client'], description='User role (optional, defaults to freelancer)')
})

google_login_response_model = auth_ns.model('GoogleLoginResponse', {
    'status': fields.String(description='Response status'),
    'message': fields.String(description='Response message'),
    'access_token': fields.String(description='JWT access token'),
    'user': fields.Nested(auth_ns.model('UserInfo', {
        'id': fields.Integer(description='User ID'),
        'email': fields.String(description='User email'),
        'role': fields.String(description='User role')
    }))
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

        # Create new user (email verification removed)
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data['role'],
            is_verified=True,  # Auto-verify since we're removing email verification
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
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
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

        # Email verification removed - all users are now auto-verified

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
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

# Email verification routes removed - using Google OAuth instead


@auth_ns.route('/google-login')
class GoogleLogin(Resource):
    @auth_ns.expect(google_login_model)
    @auth_ns.marshal_with(google_login_response_model)
    def post(self):
        """Authenticate user with Google OAuth ID token"""
        data = request.get_json()
        credential = data.get('credential')
        role = data.get('role', 'freelancer')  # Default to freelancer

        if not credential:
            logger.error("No credential provided in Google login request")
            return {'message': 'Credential is required'}, HTTPStatus.BAD_REQUEST

        try:
            # Verify the Google ID token
            google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            if not google_client_id:
                logger.error("GOOGLE_CLIENT_ID not configured")
                return {'message': 'Google OAuth not configured'}, HTTPStatus.INTERNAL_SERVER_ERROR

            idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), google_client_id)

            # Extract user info
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            name = idinfo.get('name')

            if not google_id or not email:
                logger.error("Invalid Google token: missing sub or email")
                return {'message': 'Invalid Google token'}, HTTPStatus.BAD_REQUEST

            logger.info(f"Google login attempt for email: {email}")

            # Get or create user
            user = User.get_or_create_from_google({
                'sub': google_id,
                'email': email,
                'name': name
            }, role=role)

            # Generate JWT token
            access_token = create_access_token(identity=str(user.id))

            logger.info(f"Google login successful for user {user.id}")
            return {
                'status': 'success',
                'message': 'Google login successful',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role
                }
            }, HTTPStatus.OK

        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            return {'message': 'Invalid Google token'}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            logger.error(f"Google login error: {str(e)}")
            return {'message': 'Google login failed'}, HTTPStatus.INTERNAL_SERVER_ERROR


@auth_ns.route('/me')
class UserProfile(Resource):
    @auth_ns.marshal_with(auth_ns.model('User', {
        'id': fields.Integer,
        'email': fields.String,
        'role': fields.String,
        'is_verified': fields.Boolean,
        'created_at': fields.DateTime
    }))
    @jwt_required()
    def get(self):
        """Get the authenticated user's profile"""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        logger.info(f"Profile retrieved for user {user_id}")
        return user, HTTPStatus.OK