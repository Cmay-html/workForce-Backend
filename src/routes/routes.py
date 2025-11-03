from flask import request
from flask_restx import Namespace, Resource, fields
from extensions import db, api
from auth import admin_required, create_token
from utils import paginate_query
from datetime import datetime
from sqlalchemy import func

# Import all models and their schemas cleanly from the models package
from models import (
    User, UserSchema, ClientProfile, ClientProfileSchema, FreelancerProfile, FreelancerProfileSchema,
    Project, ProjectSchema, Milestone, MilestoneSchema, Dispute, DisputeSchema,
    Deliverable, DeliverableSchema, Invoice, InvoiceSchema, Payment, PaymentSchema,
    Message, MessageSchema, Review, ReviewSchema, Skill, SkillSchema, FreelancerSkill, FreelancerSkillSchema,
    TimeLog, TimeLogSchema, ProjectApplication, ProjectApplicationSchema, Policy, PolicySchema
)

# --- Namespace Definitions ---
admin_ns = Namespace('admin', description='Admin operations')
auth_ns = Namespace('auth', description='Authentication')

# --- Swagger API Models (for documentation and validation) ---
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})
signup_model = auth_ns.model('Signup', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=True, enum=['client', 'freelancer'])
})
admin_user_model = admin_ns.model('AdminUser', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=True, enum=['client', 'freelancer', 'admin'])
})
dispute_resolution_model = admin_ns.model('DisputeResolution', {
    'resolution': fields.String(required=True)
})


def init_routes():
    """Initializes all API routes by adding namespaces to the API object."""
    api.add_namespace(admin_ns, path='/api/admin')
    api.add_namespace(auth_ns, path='/api/auth')


#Authentication Routes
@auth_ns.route('/signup')
class Signup(Resource):
    @auth_ns.expect(signup_model, validate=True)
    def post(self):
        from utils import send_verification_email
        from flask import request, current_app
        import logging

        data = request.json

        # Input validation
        if not data.get('email') or not data.get('password') or not data.get('role'):
            return {'message': 'Email, password, and role are required'}, 400

        if len(data['password']) < 8:
            return {'message': 'Password must be at least 8 characters long'}, 400

        if data['role'] not in ['client', 'freelancer']:
            return {'message': 'Role must be either client or freelancer'}, 400

        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            current_app.logger.warning(f"Signup attempt with existing email: {data['email']}")
            return {'message': 'Email already registered'}, 400

        try:
            # Create new user
            new_user = User(email=data['email'], role=data['role'])
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()

            current_app.logger.info(f"New user registered: {new_user.email} (ID: {new_user.id})")

            # Send verification email
            base_url = request.host_url.rstrip('/')
            if send_verification_email(new_user, base_url):
                current_app.logger.info(f"Verification email sent to: {new_user.email}")
                return {'message': 'Registration successful. Please check your email to verify your account.'}, 201
            else:
                current_app.logger.error(f"Failed to send verification email to: {new_user.email}")
                return {'message': 'Registration successful, but failed to send verification email. Please contact support.'}, 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during user registration: {str(e)}")
            return {'message': 'Registration failed. Please try again.'}, 500

@auth_ns.route('/verify-email')
class VerifyEmail(Resource):
    def get(self):
        from flask import current_app
        import logging

        token = request.args.get('token')
        email = request.args.get('email')

        # Input validation
        if not token or not email:
            current_app.logger.warning("Email verification attempt with missing token or email")
            return {'message': 'Invalid verification link'}, 400

        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                current_app.logger.warning(f"Email verification attempt for non-existent user: {email}")
                return {'message': 'User not found'}, 404

            if user.is_verified:
                current_app.logger.info(f"Email verification attempt for already verified user: {email}")
                return {'message': 'Email already verified'}, 200

            if user.verify_email_token(token):
                db.session.commit()
                current_app.logger.info(f"Email verified successfully for user: {email} (ID: {user.id})")
                return {'message': 'Email verified successfully'}, 200
            else:
                current_app.logger.warning(f"Invalid or expired verification token for user: {email}")
                return {'message': 'Invalid or expired verification token'}, 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during email verification: {str(e)}")
            return {'message': 'Verification failed. Please try again.'}, 500

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    def post(self):
        from flask import current_app
        import logging

        data = request.json

        # Input validation
        if not data.get('email') or not data.get('password'):
            return {'message': 'Email and password are required'}, 400

        try:
            user = User.query.filter_by(email=data['email']).first()

            if not user:
                current_app.logger.warning(f"Login attempt with non-existent email: {data['email']}")
                return {'message': 'Invalid credentials'}, 401

            if not user.check_password(data['password']):
                current_app.logger.warning(f"Failed login attempt for user: {data['email']}")
                return {'message': 'Invalid credentials'}, 401

            if not user.is_verified:
                current_app.logger.info(f"Login attempt for unverified user: {data['email']}")
                return {'message': 'Please verify your email before logging in'}, 403

            # Successful login
            token = create_token(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            current_app.logger.info(f"Successful login for user: {data['email']} (ID: {user.id})")
            return {'token': token}, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during login: {str(e)}")
            return {'message': 'Login failed. Please try again.'}, 500


# Corrected Admin CRUD Route Generation 

# A dictionary mapping API endpoints to their respective Model and Schema
MODELS_CRUD = {
    'users': (User, UserSchema),
    'disputes': (Dispute, DisputeSchema),
    'projects': (Project, ProjectSchema),
    'milestones': (Milestone, MilestoneSchema),
    'client_profiles': (ClientProfile, ClientProfileSchema),
    'freelancer_profiles': (FreelancerProfile, FreelancerProfileSchema),
    'policies': (Policy, PolicySchema),
    # Add other models here for automatic GET/DELETE endpoint creation
}

# This factory function creates the resource classes with the correct model and schema,
# solving the late binding closure problem.
def create_admin_resource(model_cls, schema_cls):
    class AdminList(Resource):
        @admin_required
        def get(self):
            """Lists all items for a given model."""
            pagination = model_cls.query.paginate(page=request.args.get('page', 1, type=int), per_page=10, error_out=False)
            return paginate_query(pagination, schema_cls(many=True))

    class AdminResource(Resource):
        @admin_required
        def get(self, id):
            """Gets a single item by ID."""
            instance = model_cls.query.get_or_404(id)
            return schema_cls().dump(instance)

        @admin_required
        def delete(self, id):
            """Deletes an item by ID."""
            instance = model_cls.query.get_or_404(id)
            db.session.delete(instance)
            db.session.commit()
            return {'message': f'Item deleted successfully.'}, 200

    return AdminList, AdminResource


# This loop now correctly assigns the generated resource classes to each endpoint
for endpoint, (model_class, schema_class) in MODELS_CRUD.items():
    ListResource, DetailResource = create_admin_resource(model_class, schema_class)
    admin_ns.add_resource(ListResource, f'/{endpoint}', endpoint=f'{endpoint}_list')
    admin_ns.add_resource(DetailResource, f'/{endpoint}/<int:id>', endpoint=f'{endpoint}_detail')


# --- Specific Routes with Custom Logic (like POST for users) ---

@admin_ns.route('/users')
class UserActions(Resource):
    # This class adds the custom POST method to the /users endpoint
    @admin_ns.expect(admin_user_model, validate=True)
    @admin_required
    def post(self):
        """Creates a new user."""
        data = request.json
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already registered'}, 400
        
        new_user = User(email=data['email'], role=data.get('role', 'client'))
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return UserSchema().dump(new_user), 201


@admin_ns.route('/disputes/<int:dispute_id>/resolve')
class AdminDisputeResolve(Resource):
    @admin_ns.expect(dispute_resolution_model, validate=True)
    @admin_required
    def put(self, dispute_id):
        """Resolves a dispute."""
        dispute = Dispute.query.get_or_404(dispute_id)
        data = request.json
        dispute.resolution = data.get('resolution')
        dispute.status = 'resolved'
        dispute.resolved_at = datetime.utcnow()
        db.session.commit()
        return DisputeSchema().dump(dispute)


@admin_ns.route('/analytics')
class AdminAnalytics(Resource):
    @admin_required
    def get(self):
        """Gets key analytics data."""
        total_users = db.session.query(func.count(User.id)).scalar()
        ongoing_projects = db.session.query(func.count(Project.id)).filter(Project.status == 'active').scalar()
        revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'processed').scalar() or 0
        return {
            'total_users': total_users,
            'ongoing_projects': ongoing_projects,
            'revenue': float(revenue)
        }