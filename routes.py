# routes.py
from flask_restx import Namespace, Resource, fields, abort
from extensions import api, db
from models import Deliverable, Invoice, Message, Milestone, Payment, ProjectApplication, Project, Review, Skill, FreelancerSkill, TimeLog, User, FreelancerProfile, ClientProfile, Dispute, Policy
from models import DeliverableSchema, InvoiceSchema, MessageSchema, MilestoneSchema, PaymentSchema, ProjectApplicationSchema, ProjectSchema, ReviewSchema, SkillSchema, FreelancerSkillSchema, TimeLogSchema, UserSchema, FreelancerProfileSchema, ClientProfileSchema, DisputeSchema, PolicySchema
from auth import admin_required, create_token
from utils import paginate_query, send_email, upload_file
from flask import request
from datetime import datetime
from sqlalchemy import func

admin_ns = Namespace('admin', description='Admin operations')
auth_ns = Namespace('auth', description='Authentication')

# Swagger Models
user_model = admin_ns.model('User', {
    'id': fields.Integer(readonly=True),
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=True, enum=['client', 'freelancer', 'admin']),
    'is_verified': fields.Boolean(),
    'last_login': fields.DateTime()
})

# Model for admin-created users (requires email & password, role optional)
admin_user_model = admin_ns.model('AdminUser', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=False, enum=['client', 'freelancer', 'admin']),
    'is_verified': fields.Boolean()
})

# Auth models (separate from admin user model so login/register don't require admin-only fields)
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})

register_model = auth_ns.model('Register', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
    'role': fields.String(required=False, enum=['client', 'freelancer', 'admin']),
    'is_verified': fields.Boolean(required=False)
})

client_profile_model = admin_ns.model('ClientProfile', {
    'id': fields.Integer(readonly=True),
    'user_id': fields.Integer(required=True),
    'company_name': fields.String(),
    'industry': fields.String(),
    'bio': fields.String(),
    'website': fields.String(),
    'profile_picture_uri': fields.String()
})

freelancer_profile_model = admin_ns.model('FreelancerProfile', {
    'id': fields.Integer(readonly=True),
    'user_id': fields.Integer(required=True),
    'hourly_rate': fields.Float(),
    'bio': fields.String(),
    'experience': fields.String(),
    'portfolio_links': fields.String(),
    'profile_picture_uri': fields.String()
})

project_model = admin_ns.model('Project', {
    'id': fields.Integer(readonly=True),
    'title': fields.String(required=True),
    'description': fields.String(),
    'budget': fields.Float(),
    'status': fields.String(),
    'client_id': fields.Integer(),
    'freelancer_id': fields.Integer()
})

project_application_model = admin_ns.model('ProjectApplication', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'freelancer_id': fields.Integer(required=True),
    'status': fields.String()
})

milestone_model = admin_ns.model('Milestone', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'title': fields.String(required=True),
    'description': fields.String(),
    'due_date': fields.Date(),
    'amount': fields.Float(),
    'status': fields.String()
})

deliverable_model = admin_ns.model('Deliverable', {
    'id': fields.Integer(readonly=True),
    'milestone_id': fields.Integer(required=True),
    'file_url': fields.String(),
    'link': fields.String(),
    'status': fields.String()
})

invoice_model = admin_ns.model('Invoice', {
    'id': fields.Integer(readonly=True),
    'milestone_id': fields.Integer(required=True),
    'amount': fields.Float(),
    'status': fields.String()
})

payment_model = admin_ns.model('Payment', {
    'id': fields.Integer(readonly=True),
    'invoice_id': fields.Integer(required=True),
    'client_id': fields.Integer(required=True),
    'transaction_id': fields.String(),
    'amount': fields.Float(),
    'status': fields.String()
})

message_model = admin_ns.model('Message', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'sender_id': fields.Integer(required=True),
    'receiver_id': fields.Integer(required=True),
    'content': fields.String(),
    'attachment_url': fields.String(),
    'is_approved': fields.Boolean()
})

review_model = admin_ns.model('Review', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'reviewer_id': fields.Integer(required=True),
    'rating': fields.Integer(),
    'comment': fields.String()
})

skill_model = admin_ns.model('Skill', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True)
})

freelancer_skill_model = admin_ns.model('FreelancerSkill', {
    'id': fields.Integer(readonly=True),
    'freelancer_profile_id': fields.Integer(required=True),
    'skill_id': fields.Integer(required=True)
})

time_log_model = admin_ns.model('TimeLog', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'freelancer_id': fields.Integer(required=True),
    'start_time': fields.DateTime(),
    'end_time': fields.DateTime()
})

dispute_model = admin_ns.model('Dispute', {
    'id': fields.Integer(readonly=True),
    'milestone_id': fields.Integer(required=True),
    'description': fields.String(),
    'resolution': fields.String(),
    'status': fields.String(),
    'resolved_at': fields.DateTime()
})

policy_model = admin_ns.model('Policy', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'content': fields.String()
})

# Model used when resolving a dispute (only resolution required)
dispute_resolution_model = admin_ns.model('DisputeResolution', {
    'resolution': fields.String(required=True)
})

def init_routes():
    api.add_namespace(admin_ns, path='/api/admin')
    api.add_namespace(auth_ns, path='/api/auth')

# Authentication Routes
@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model, validate=True)
    def post(self):
        data = request.json
        if User.query.filter_by(email=data['email']).first():
            abort(400, message='Email already registered')
        user = User(email=data['email'])
        user.set_password(data['password'])
        user.role = data.get('role', 'client')
        user.is_verified = data.get('is_verified', False)
        db.session.add(user)
        db.session.commit()
        token = create_token(user)
        send_email(data['email'], 'Welcome to FreelanceFlow', 'Please verify your account.')
        return {'token': token}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    def post(self):
        data = request.json
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            token = create_token(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return {'token': token}, 200
        abort(401, message='Invalid credentials')

# Admin CRUD Routes
models = {
    'users': (User, UserSchema, admin_user_model),
    'client_profiles': (ClientProfile, ClientProfileSchema, client_profile_model),
    'freelancer_profiles': (FreelancerProfile, FreelancerProfileSchema, freelancer_profile_model),
    'projects': (Project, ProjectSchema, project_model),
    'project_applications': (ProjectApplication, ProjectApplicationSchema, project_application_model),
    'milestones': (Milestone, MilestoneSchema, milestone_model),
    'deliverables': (Deliverable, DeliverableSchema, deliverable_model),
    'invoices': (Invoice, InvoiceSchema, invoice_model),
    'payments': (Payment, PaymentSchema, payment_model),
    'messages': (Message, MessageSchema, message_model),
    'reviews': (Review, ReviewSchema, review_model),
    'skills': (Skill, SkillSchema, skill_model),
    'freelancer_skills': (FreelancerSkill, FreelancerSkillSchema, freelancer_skill_model),
    'time_logs': (TimeLog, TimeLogSchema, time_log_model),
    'disputes': (Dispute, DisputeSchema, dispute_model),
    'policies': (Policy, PolicySchema, policy_model)
}

for endpoint, (model, schema, swagger_model) in models.items():
    @admin_ns.route(f'/{endpoint}')
    class AdminList(Resource):
        @admin_ns.doc(f'list_{endpoint[:-1] if endpoint.endswith("s") else endpoint}')
        @admin_required()
        def get(self):
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            pagination = model.query.paginate(page=page, per_page=per_page, error_out=False)
            return paginate_query(pagination, schema(many=True))

        @admin_ns.doc(f'create_{endpoint[:-1] if endpoint.endswith("s") else endpoint}')
        @admin_ns.expect(swagger_model, validate=True)
        @admin_required()
        def post(self):
            data = request.json
            # Handle password hashing for User model
            if model == User:
                # If frontend provides a password, use it. Otherwise generate a temporary one.
                if 'password' in data and data['password']:
                    instance = model(email=data['email'])
                    instance.set_password(data['password'])
                    for key, value in data.items():
                        if key not in ['password'] and hasattr(instance, key):
                            setattr(instance, key, value)
                    db.session.add(instance)
                    db.session.commit()
                    return schema().dump(instance), 201
                else:
                    # Create user with a generated temporary password and return it to the admin
                    import secrets
                    temp_pw = secrets.token_urlsafe(8)
                    instance = model(email=data.get('email'))
                    instance.set_password(temp_pw)
                    for key, value in data.items():
                        if key not in ['password'] and hasattr(instance, key):
                            setattr(instance, key, value)
                    db.session.add(instance)
                    db.session.commit()
                    result = schema().dump(instance)
                    result['generated_password'] = temp_pw
                    return result, 201
            else:
                instance = model(**{k: v for k, v in data.items() if hasattr(model, k)})
            db.session.add(instance)
            db.session.commit()
            return schema().dump(instance), 201

    @admin_ns.route(f'/{endpoint}/<int:id>')
    class AdminResource(Resource):
        @admin_ns.doc(f'get_{endpoint[:-1] if endpoint.endswith("s") else endpoint}')
        @admin_required()
        def get(self, id):
            instance = model.query.get_or_404(id)
            return schema().dump(instance)

        @admin_ns.doc(f'update_{endpoint[:-1] if endpoint.endswith("s") else endpoint}')
        @admin_ns.expect(swagger_model, validate=True)
        @admin_required()
        def put(self, id):
            instance = model.query.get_or_404(id)
            data = request.json
            if model == User and 'password' in data:
                instance.set_password(data['password'])
                del data['password']  # Avoid setting password as plain text attribute
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            db.session.commit()
            return schema().dump(instance)

        @admin_ns.doc(f'delete_{endpoint[:-1] if endpoint.endswith("s") else endpoint}')
        @admin_required()
        def delete(self, id):
            instance = model.query.get_or_404(id)
            db.session.delete(instance)
            db.session.commit()
            return {'message': f'{endpoint[:-1] if endpoint.endswith("s") else endpoint} deleted'}, 200

# Message Moderation
@admin_ns.route('/messages/<int:message_id>/approve')
class AdminMessageApprove(Resource):
    @admin_ns.doc('approve_message')
    @admin_required()
    def put(self, message_id):
        message = Message.query.get_or_404(message_id)
        message.is_approved = True
        db.session.commit()
        send_email(f'user{message.sender_id}@example.com', 'Message Approved', 'Your message has been approved.')
        return MessageSchema().dump(message)

# Dispute Resolution
@admin_ns.route('/disputes/<int:dispute_id>/resolve')
class AdminDisputeResolve(Resource):
    @admin_ns.doc('resolve_dispute')
    @admin_ns.expect(dispute_resolution_model, validate=True)
    @admin_required()
    def put(self, dispute_id):
        dispute = Dispute.query.get_or_404(dispute_id)
        data = request.json
        dispute.resolution = data.get('resolution')
        dispute.status = 'resolved'
        dispute.resolved_at = datetime.utcnow()
        db.session.commit()
        send_email('client@example.com', 'Dispute Resolved', dispute.resolution)
        return DisputeSchema().dump(dispute)

# Policy Updates
@admin_ns.route('/policies/<int:policy_id>')
class AdminPolicyUpdate(Resource):
    @admin_ns.doc('update_policy')
    @admin_ns.expect(policy_model, validate=True)
    @admin_required()
    def put(self, policy_id):
        policy = Policy.query.get_or_404(policy_id)
        data = request.json
        policy.content = data.get('content', policy.content)
        db.session.commit()
        return PolicySchema().dump(policy)

# Analytics
@admin_ns.route('/analytics')
class AdminAnalytics(Resource):
    @admin_ns.doc('get_analytics')
    @admin_required()
    def get(self):
        total_users = db.session.query(func.count(User.id)).scalar()
        ongoing_projects = db.session.query(func.count(Project.id)).filter(Project.status == 'active').scalar()
        revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'processed').scalar() or 0
        return {
            'total_users': total_users,
            'ongoing_projects': ongoing_projects,
            'revenue': float(revenue) if revenue else 0.0
        }