# routes/freelancer.py
from flask import request
from flask_restx import Namespace, Resource, reqparse, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.extensions import db
from src.models.user import FreelancerProfile, User
from src.models.project_application import ProjectApplication
from src.models.project import Project
from http import HTTPStatus
import logging

logger = logging.getLogger(__name__)
ns = Namespace('freelancer', description='Freelancer Journey')

def require_role(role):
    def decorator(f):
        @jwt_required()
        def wrapped(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != role:
                logger.error(f"Unauthorized access by {get_jwt_identity()} with role {claims.get('role')}")
                return {'message': f'Only {role}s allowed'}, HTTPStatus.FORBIDDEN
            user_email = get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
            if not user or not user.freelancer_profile:
                logger.error(f"Freelancer profile not found for {user_email}")
                return {'message': 'Profile not found'}, HTTPStatus.NOT_FOUND
            request.user = user.freelancer_profile
            return f(*args, **kwargs)
        return wrapped
    return decorator

# API Models
profile_model = ns.model('FreelancerProfile', {
    'id': fields.Integer(readonly=True),
    'user_id': fields.Integer(readonly=True),
    'hourly_rate': fields.Float(),
    'bio': fields.String(),
    'experience': fields.String(),
    'portfolio_links': fields.String(),
    'profile_picture_uri': fields.String(),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

project_model = ns.model('Project', {
    'id': fields.Integer(readonly=True),
    'title': fields.String(),
    'description': fields.String(),
    'budget': fields.Float(),
    'status': fields.String(),
    'client_id': fields.Integer(),
    'freelancer_id': fields.Integer(),
    'created_at': fields.DateTime(),
    'completed_at': fields.DateTime()
})

application_model = ns.model('Application', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(),
    'freelancer_id': fields.Integer(),
    'proposal': fields.String(),
    'bid_amount': fields.Float(),
    'status': fields.String(),
    'applied_at': fields.DateTime()
})

@ns.route('/profile')
class FreelancerProfile(Resource):
    @ns.marshal_with(profile_model)
    @require_role('freelancer')
    def get(self):
        """Get freelancer profile"""
        freelancer = request.user
        logger.info(f"Freelancer {freelancer.id} retrieved profile")
        return freelancer, HTTPStatus.OK

    @ns.expect(profile_model)
    @ns.marshal_with(profile_model)
    @require_role('freelancer')
    def put(self):
        """Update freelancer profile"""
        freelancer = request.user
        data = request.get_json()

        # Update allowed fields
        updatable_fields = ['hourly_rate', 'bio', 'experience', 'portfolio_links', 'profile_picture_uri']
        for field in updatable_fields:
            if field in data:
                setattr(freelancer, field, data[field])

        freelancer.updated_at = db.func.now()
        db.session.commit()
        logger.info(f"Freelancer {freelancer.id} updated profile")
        return freelancer, HTTPStatus.OK

@ns.route('/projects')
class FreelancerProjects(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, default=1)
    parser.add_argument('per_page', type=int, default=10)
    parser.add_argument('status', type=str, choices=['posted', 'active', 'completed'])

    @ns.expect(parser)
    @ns.marshal_list_with(project_model, envelope='data')
    @require_role('freelancer')
    def get(self):
        """Get available projects or freelancer's projects"""
        args = self.parser.parse_args()
        freelancer = request.user

        query = Project.query

        if args['status']:
            if args['status'] == 'posted':
                # Available projects
                query = query.filter(Project.status.in_(['posted', 'open']))
            elif args['status'] == 'active':
                # Freelancer's active projects
                query = query.filter_by(freelancer_id=freelancer.id, status='active')
            elif args['status'] == 'completed':
                # Freelancer's completed projects
                query = query.filter_by(freelancer_id=freelancer.id, status='completed')
        else:
            # Default: available projects + freelancer's projects
            query = query.filter(
                (Project.status.in_(['posted', 'open'])) |
                (Project.freelancer_id == freelancer.id)
            )

        projects = query.order_by(Project.created_at.desc()).paginate(
            page=args['page'], per_page=args['per_page'], error_out=False
        )

        logger.info(f"Freelancer {freelancer.id} retrieved {len(projects.items)} projects")
        return projects.items, HTTPStatus.OK

@ns.route('/applications')
class FreelancerApplications(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, default=1)
    parser.add_argument('per_page', type=int, default=10)

    @ns.expect(parser)
    @ns.marshal_list_with(application_model, envelope='data')
    @require_role('freelancer')
    def get(self):
        args = self.parser.parse_args()
        freelancer = request.user
        applications = ProjectApplication.query.filter_by(freelancer_id=freelancer.id).paginate(
            page=args['page'], per_page=args['per_page'], error_out=False
        )
        logger.info(f"Freelancer {freelancer.id} retrieved applications")
        return applications.items, HTTPStatus.OK

@ns.route('/projects/<int:project_id>/apply')
class ApplyToProject(Resource):
    application_fields = ns.model('ApplyModel', {
        'proposal': fields.String(description='Proposal text'),
        'bid_amount': fields.Float(description='Bid amount')
    })

    @ns.expect(application_fields)
    @require_role('freelancer')
    def post(self, project_id):
        """Apply to a project"""
        freelancer = request.user
        data = request.get_json()

        # Check if project exists and is available
        project = Project.query.filter_by(id=project_id, status='posted').first()
        if not project:
            return {'message': 'Project not found or not available'}, HTTPStatus.NOT_FOUND

        # Check if already applied
        existing_app = ProjectApplication.query.filter_by(
            project_id=project_id, freelancer_id=freelancer.id
        ).first()
        if existing_app:
            return {'message': 'Already applied to this project'}, HTTPStatus.BAD_REQUEST

        # Create application
        application = ProjectApplication(
            project_id=project_id,
            freelancer_id=freelancer.id,
            proposal=data.get('proposal'),
            bid_amount=data.get('bid_amount'),
            status='pending'
        )

        db.session.add(application)
        db.session.commit()
        logger.info(f"Freelancer {freelancer.id} applied to project {project_id}")
        return {'message': 'Application submitted successfully', 'application_id': application.id}, HTTPStatus.CREATED

def register_routes(api_ns):
    pass