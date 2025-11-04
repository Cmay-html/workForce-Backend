# routes/projects.py
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Project, ProjectApplication, User

# Create namespace
projects_ns = Namespace('projects', description='Project operations')
api = projects_ns  # For compatibility with existing code

# API models for Swagger documentation
project_model = api.model('Project', {
    'id': fields.Integer(readonly=True, description='Project ID'),
    'title': fields.String(required=True, description='Project title'),
    'description': fields.String(required=True, description='Project description'),
    'budget': fields.Float(required=True, description='Project budget'),
    'status': fields.String(description='Project status'),
    'client_id': fields.Integer(readonly=True, description='Client ID'),
    'freelancer_id': fields.Integer(description='Freelancer ID'),
    'created_at': fields.String(description='Creation date'),
    'completed_at': fields.String(description='Completion date')
})

project_create_model = api.model('ProjectCreate', {
    'title': fields.String(required=True, description='Project title'),
    'description': fields.String(required=True, description='Project description'),
    'budget': fields.Float(required=True, description='Project budget')
})

hire_model = api.model('HireFreelancer', {
    'freelancer_id': fields.Integer(required=True, description='Freelancer ID to hire')
})


@api.route('/')
class ProjectList(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @jwt_required()
    def get(self):
        """Get projects based on user role"""
        try:
            current_user_id = get_jwt_identity()

            # Get current user with role
            current_user = User.query.get(int(current_user_id))
            if not current_user:
                return {
                    'success': False,
                    'message': 'User not found'
                }, 404

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # Role-based project filtering
            if current_user.role == 'client':
                # Clients see their own projects - use client_profile.id
                if not current_user.client_profile:
                    return {
                        'success': False,
                        'message': 'Client profile not found'
                    }, 400
                query = Project.query.filter_by(client_id=current_user.client_profile.id)
            elif current_user.role == 'freelancer':
                # Freelancers see available projects and their assigned projects
                freelancer_id = current_user.freelancer_profile.id if current_user.freelancer_profile else None
                query = Project.query.filter(
                    (Project.status.in_(['posted', 'active'])) |
                    (Project.freelancer_id == freelancer_id)
                )
            else:  # admin or other roles
                query = Project.query

            projects = query.order_by(Project.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)

            return {
                'success': True,
                'data': [project.to_dict() for project in projects.items],
                'pagination': {
                    'page': projects.page,
                    'per_page': projects.per_page,
                    'total': projects.total,
                    'pages': projects.pages
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching projects: {str(e)}'
            }, 500

    @api.doc(security='Bearer Auth')
    @api.expect(project_create_model)
    @api.response(201, 'Project created successfully')
    @api.response(400, 'Validation error')
    @api.response(403, 'Forbidden - Client role required')
    @jwt_required()
    def post(self):
        """Create a new project (Client only)"""
        try:
            current_user_id = get_jwt_identity()

            # Get current user with role - cast to int since JWT identity is string
            current_user = User.query.get(int(current_user_id))
            if not current_user:
                return {
                    'success': False,
                    'message': 'User not found'
                }, 404

            # Only clients can create projects
            if current_user.role != 'client':
                return {
                    'success': False,
                    'message': 'Only clients can create projects'
                }, 403

            # Check that user has a client_profile
            if not current_user.client_profile:
                return {
                    'success': False,
                    'message': 'Client profile not found. Please contact support.'
                }, 400

            data = request.get_json()

            # Validate required fields
            required_fields = ['title', 'description', 'budget']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required'
                    }, 400

            # Create project - use client_profile.id instead of user.id
            project = Project(
                title=data['title'],
                description=data['description'],
                client_id=current_user.client_profile.id,  # FIX: Use client_profile.id
                budget=data['budget'],
                status='draft'
            )

            db.session.add(project)
            db.session.commit()

            return {
                'success': True,
                'data': project.to_dict(),
                'message': 'Project created successfully'
            }, 201

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error creating project: {str(e)}'
            }, 400


@api.route('/<int:project_id>')
class ProjectResource(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Project not found')
    @jwt_required()
    def get(self, project_id):
        """Get a specific project"""
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(int(current_user_id))
            project = Project.query.get_or_404(project_id)

            # Authorization check based on role
            if current_user.role == 'client':
                # Clients can only see their own projects
                client_profile_id = current_user.client_profile.id if current_user.client_profile else None
                if project.client_id != client_profile_id:
                    return {
                        'success': False,
                        'message': 'Not authorized to access this project'
                    }, 403
            elif current_user.role == 'freelancer':
                # Freelancers can see projects they're assigned to or available projects
                freelancer_profile_id = current_user.freelancer_profile.id if current_user.freelancer_profile else None
                if project.freelancer_id != freelancer_profile_id and project.status not in ['posted', 'active']:
                    return {
                        'success': False,
                        'message': 'Not authorized to access this project'
                    }, 403
            # Admin can view any project

            return {
                'success': True,
                'data': project.to_dict()
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching project: {str(e)}'
            }, 500

    @api.doc(security='Bearer Auth')
    @api.expect(project_create_model)
    @api.response(200, 'Project updated successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Project not found')
    @jwt_required()
    def put(self, project_id):
        """Update a project"""
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(int(current_user_id))
            project = Project.query.get_or_404(project_id)

            # Only project client can update projects
            client_profile_id = current_user.client_profile.id if current_user.client_profile else None
            if current_user.role != 'client' or project.client_id != client_profile_id:
                return {
                    'success': False,
                    'message': 'Not authorized to update this project'
                }, 403

            data = request.get_json()

            # Update fields
            updatable_fields = ['title', 'description', 'budget']
            for field in updatable_fields:
                if field in data:
                    setattr(project, field, data[field])

            db.session.commit()

            return {
                'success': True,
                'data': project.to_dict(),
                'message': 'Project updated successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error updating project: {str(e)}'
            }, 400


@api.route('/<int:project_id>/applications')
class ProjectApplications(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def get(self, project_id):
        """Get all applications for a project"""
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(int(current_user_id))
            project = Project.query.get_or_404(project_id)

            # Authorization check
            if current_user.role == 'client':
                # Only project client can view applications
                client_profile_id = current_user.client_profile.id if current_user.client_profile else None
                if project.client_id != client_profile_id:
                    return {
                        'success': False,
                        'message': 'Not authorized to view applications for this project'
                    }, 403
            elif current_user.role == 'freelancer':
                # Freelancers can only see their own applications
                # This would require a different endpoint for freelancers
                return {
                    'success': False,
                    'message': 'Use the freelancer applications endpoint'
                }, 403
            # Admin can view any project applications

            applications = ProjectApplication.query.filter_by(project_id=project_id)\
                .join(User, ProjectApplication.freelancer_id == User.id)\
                .add_entity(User)\
                .all()

            return {
                'success': True,
                'data': [{
                    'application_id': app[0].id,
                    'freelancer': {
                        'id': app[1].id,
                        'name': f"{app[1].first_name} {app[1].last_name}",
                        'email': app[1].email
                    },
                    'proposal': app[0].proposal,
                    'bid_amount': float(app[0].bid_amount) if app[0].bid_amount else None,
                    'status': app[0].status,
                    'applied_at': app[0].created_at.isoformat() if app[0].created_at else None
                } for app in applications]
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching applications: {str(e)}'
            }, 500


@api.route('/<int:project_id>/hire')
class ProjectHire(Resource):
    @api.doc(security='Bearer Auth')
    @api.expect(hire_model)
    @api.response(200, 'Freelancer hired successfully')
    @api.response(400, 'Validation error')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def post(self, project_id):
        """Hire a freelancer for a project (Client only)"""
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get(int(current_user_id))
            project = Project.query.get_or_404(project_id)
            data = request.get_json()

            # Only project client can hire freelancers
            client_profile_id = current_user.client_profile.id if current_user.client_profile else None
            if current_user.role != 'client' or project.client_id != client_profile_id:
                return {
                    'success': False,
                    'message': 'Not authorized to hire for this project'
                }, 403

            freelancer_id = data.get('freelancer_id')
            if not freelancer_id:
                return {
                    'success': False,
                    'message': 'freelancer_id is required'
                }, 400

            # Verify freelancer exists and has applied
            application = ProjectApplication.query.filter_by(
                project_id=project_id,
                freelancer_id=freelancer_id
            ).first()

            if not application:
                return {
                    'success': False,
                    'message': 'Freelancer has not applied to this project'
                }, 400

            # Update project with hired freelancer
            project.freelancer_id = freelancer_id
            project.status = 'active'

            # Update application status
            application.status = 'hired'

            db.session.commit()

            return {
                'success': True,
                'data': project.to_dict(),
                'message': 'Freelancer hired successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error hiring freelancer: {str(e)}'
            }, 400
