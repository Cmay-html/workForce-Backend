from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User, FreelancerProfile
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

user_data_model = auth_ns.model('UserData', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(description='User email'),
    'role': fields.String(description='User role'),
    'created_at': fields.String(description='Account creation timestamp')
})

token_response_model = auth_ns.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'user': fields.Nested(user_data_model, description='User data for frontend routing', skip_none=True)
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
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logger.info(f"User {user.id} signed up successfully")
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
            }
        }, HTTPStatus.CREATED

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model)
    def post(self):
        """Authenticate a user and return JWT tokens"""
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            logger.error("Missing email or password in login request")
            return {'message': 'Email and password are required'}, HTTPStatus.BAD_REQUEST
        
        logger.info(f"Login attempt for email: {data['email']}")

        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            logger.error(f"Invalid credentials for email: {data['email']}")
            return {'message': 'Invalid email or password'}, HTTPStatus.UNAUTHORIZED

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logger.info(f"User {user.id} logged in successfully")
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
            }
        }, HTTPStatus.OK

@auth_ns.route('/admin-login')
class AdminLogin(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model)
    def post(self):
        """Admin-specific login endpoint"""
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            logger.error("Missing email or password in admin login request")
            return {'message': 'Email and password are required'}, HTTPStatus.BAD_REQUEST
        
        logger.info(f"Admin login attempt for email: {data['email']}")

        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            logger.error(f"Invalid credentials for email: {data['email']}")
            return {'message': 'Invalid email or password'}, HTTPStatus.UNAUTHORIZED

        # Verify user has admin role
        if user.role != 'admin':
            logger.error(f"Non-admin user {data['email']} attempted admin login")
            return {'message': 'Access denied. Admin privileges required.'}, HTTPStatus.FORBIDDEN

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logger.info(f"Admin user {user.id} logged in successfully")
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
            }
        }, HTTPStatus.OK

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.marshal_with(token_response_model)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh an access token using a refresh token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=str(current_user_id))
        logger.info(f"Access token refreshed for user {current_user_id}")
        return {'access_token': access_token, 'refresh_token': None}, HTTPStatus.OK

@auth_ns.route('/register/client')
class RegisterClient(Resource):
    @auth_ns.expect(auth_ns.model('ClientSignup', {
        'email': fields.String(required=True, description='User email address'),
        'password': fields.String(required=True, description='User password'),
        'company_name': fields.String(required=False, description='Company name'),
        'industry': fields.String(required=False, description='Industry')
    }))
    @auth_ns.marshal_with(token_response_model, code=HTTPStatus.CREATED, description='Returns access and refresh tokens')
    def post(self):
        """Register a new client user with profile"""
        data = request.get_json()
        logger.info(f"Client registration attempt for email: {data['email']}")

        # Validate email uniqueness
        if User.query.filter_by(email=data['email']).first():
            logger.error(f"Email {data['email']} already exists")
            return {'message': 'Email already exists'}, HTTPStatus.BAD_REQUEST

        # Create new client user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='client',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create client profile
        from ..models import ClientProfile
        client_profile = ClientProfile(
            user_id=user.id,
            company_name=data.get('company_name'),
            industry=data.get('industry'),
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(client_profile)
        db.session.commit()

        # Generate JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logger.info(f"Client {user.id} registered successfully")
        # Also return minimal user payload to allow frontend redirect by role
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
            }
        }, HTTPStatus.CREATED

@auth_ns.route('/register/freelancer')
class RegisterFreelancer(Resource):
    @auth_ns.expect(auth_ns.model('FreelancerSignup', {
        'email': fields.String(required=True, description='User email address'),
        'password': fields.String(required=True, description='User password'),
        'hourly_rate': fields.Float(required=False, description='Hourly rate'),
        'bio': fields.String(required=False, description='Bio'),
        'skills': fields.List(fields.String, required=False, description='List of skill names')
    }))
    @auth_ns.marshal_with(token_response_model, code=HTTPStatus.CREATED, description='Returns access and refresh tokens')
    def post(self):
        """Register a new freelancer user with profile"""
        data = request.get_json()
        logger.info(f"Freelancer registration attempt for email: {data['email']}")

        # Validate email uniqueness
        if User.query.filter_by(email=data['email']).first():
            logger.error(f"Email {data['email']} already exists")
            return {'message': 'Email already exists'}, HTTPStatus.BAD_REQUEST

        # Create new freelancer user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='freelancer',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create freelancer profile
        freelancer_profile = FreelancerProfile(
            user_id=user.id,
            hourly_rate=data.get('hourly_rate'),
            bio=data.get('bio'),
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(freelancer_profile)
        db.session.flush()
        
        # Handle skills if provided
        if data.get('skills'):
            from ..models import Skill
            for skill_name in data['skills']:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                freelancer_profile.skills.append(skill)
        
        db.session.commit()

        # Generate JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logger.info(f"Freelancer {user.id} registered successfully")
        # Also return minimal user payload to allow frontend redirect by role
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
            }
        }, HTTPStatus.CREATED

@auth_ns.route('/me')
class UserProfile(Resource):
    @jwt_required()
    def get(self):
        """Get the authenticated user's profile"""
        user_id = get_jwt_identity()
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            uid = user_id
        user = User.query.get_or_404(uid)
        logger.info(f"Profile retrieved for user {user_id}")
        return {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
        }, HTTPStatus.OK

@auth_ns.route('/whoami')
class WhoAmI(Resource):
    @jwt_required()
    def get(self):
        identity = get_jwt_identity()
        return {'identity': identity}, HTTPStatus.OK

admin_creation_model = auth_ns.model('AdminCreation', {
    'email': fields.String(required=True, description='Admin email address'),
    'password': fields.String(required=True, description='Admin password'),
    'secret_key': fields.String(required=True, description='Admin creation secret key')
})

@auth_ns.route('/create-admin')
class CreateAdmin(Resource):
    @auth_ns.expect(admin_creation_model)
    @auth_ns.marshal_with(token_response_model, code=HTTPStatus.CREATED)
    def post(self):
        """Create an admin user (requires secret key)"""
        import os
        data = request.get_json()
        
        # Verify secret key
        ADMIN_SECRET = os.getenv('ADMIN_CREATION_SECRET', 'your-super-secret-admin-key-2024')
        if data.get('secret_key') != ADMIN_SECRET:
            logger.error("Invalid admin creation secret key")
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        
        logger.info(f"Admin creation attempt for email: {data['email']}")
        
        # Check if admin already exists
        if User.query.filter_by(email=data['email']).first():
            logger.error(f"Email {data['email']} already exists")
            return {'message': 'Email already exists'}, HTTPStatus.BAD_REQUEST
        
        # Create admin user
        admin = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='admin',
            is_verified=True,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(admin)
        db.session.commit()
        
        logger.info(f"Admin user created successfully: {admin.email}")
        
        # Generate tokens
        access_token = create_access_token(identity=str(admin.id))
        refresh_token = create_refresh_token(identity=str(admin.id))
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': admin.id,
                'email': admin.email,
                'role': admin.role,
                'created_at': admin.created_at.isoformat()
            }
        }, HTTPStatus.CREATED