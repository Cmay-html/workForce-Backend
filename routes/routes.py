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
        from flask import request

        data = request.json
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already registered'}, 400

        new_user = User(email=data['email'], role=data['role'])
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        base_url = request.host_url.rstrip('/')
        if send_verification_email(new_user, base_url):
            return {'message': 'Registration successful. Please check your email to verify your account.'}, 201
        else:
            return {'message': 'Registration successful, but failed to send verification email. Please contact support.'}, 201

@auth_ns.route('/verify-email')
class VerifyEmail(Resource):
    def get(self):
        token = request.args.get('token')
        email = request.args.get('email')

        if not token or not email:
            return {'message': 'Invalid verification link'}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'User not found'}, 404

        if user.verify_email_token(token):
            db.session.commit()
            return {'message': 'Email verified successfully'}, 200
        else:
            return {'message': 'Invalid or expired verification token'}, 400

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    def post(self):
        data = request.json
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            if not user.is_verified:
                return {'message': 'Please verify your email before logging in'}, 403

            token = create_token(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return {'token': token}, 200
        return {'message': 'Invalid credentials'}, 401


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