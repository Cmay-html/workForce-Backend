# routes/milestone.py
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Milestone, Project, User
from datetime import datetime

# Create namespace
api = Namespace('milestones', description='Milestone operations')

# API models for Swagger documentation
milestone_model = api.model('Milestone', {
    'id': fields.Integer(readonly=True, description='Milestone ID'),
    'project_id': fields.Integer(required=True, description='Project ID'),
    'title': fields.String(required=True, description='Milestone title'),
    'description': fields.String(required=True, description='Milestone description'),
    'due_date': fields.String(required=True, description='Due date (YYYY-MM-DD)'),
    'amount': fields.Float(required=True, description='Milestone amount'),
    'status': fields.String(description='Milestone status')
})

milestone_create_model = api.model('MilestoneCreate', {
    'project_id': fields.Integer(required=True, description='Project ID'),
    'title': fields.String(required=True, description='Milestone title'),
    'description': fields.String(required=True, description='Milestone description'),
    'due_date': fields.String(required=True, description='Due date (YYYY-MM-DD)'),
    'amount': fields.Float(required=True, description='Milestone amount')
})

milestone_update_model = api.model('MilestoneUpdate', {
    'title': fields.String(description='Milestone title'),
    'description': fields.String(description='Milestone description'),
    'due_date': fields.String(description='Due date (YYYY-MM-DD)'),
    'amount': fields.Float(description='Milestone amount'),
    'status': fields.String(description='Milestone status')
})


@api.route('/')
class MilestoneList(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get all milestones for current user's projects"""
        try:
            current_user_id = get_jwt_identity()

            # Get current user with role information
            current_user = User.query.get(current_user_id)
            if not current_user:
                return {
                    'success': False,
                    'message': 'User not found'
                }, 404

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # Get projects based on user role
            if current_user.role == 'client':
                user_projects = Project.query.filter_by(
                    client_id=current_user_id)
            elif current_user.role == 'freelancer':
                user_projects = Project.query.filter_by(
                    freelancer_id=current_user_id)
            else:  # admin or other roles
                user_projects = Project.query

            project_ids = [project.id for project in user_projects.all()]

            if not project_ids:
                return {
                    'success': True,
                    'data': [],
                    'pagination': {
                        'page': 1,
                        'per_page': per_page,
                        'total': 0,
                        'pages': 0
                    }
                }

            # Get milestones for these projects
            milestones = Milestone.query.filter(
                Milestone.project_id.in_(project_ids)
            ).order_by(Milestone.due_date.asc())\
             .paginate(page=page, per_page=per_page, error_out=False)

            return {
                'success': True,
                'data': [milestone.to_dict() for milestone in milestones.items],
                'pagination': {
                    'page': milestones.page,
                    'per_page': milestones.per_page,
                    'total': milestones.total,
                    'pages': milestones.pages
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching milestones: {str(e)}'
            }, 500

    @api.doc(security='Bearer Auth')
    @api.expect(milestone_create_model)
    @api.response(201, 'Milestone created successfully')
    @api.response(400, 'Validation error')
    @api.response(403, 'Forbidden - Client role required')
    @jwt_required()
    def post(self):
        """Create a new milestone for a project (Client only)"""
        try:
            current_user_id = get_jwt_identity()

            # Check if user is a client
            current_user = User.query.get(current_user_id)
            if not current_user or current_user.role != 'client':
                return {
                    'success': False,
                    'message': 'Only clients can create milestones'
                }, 403

            data = request.get_json()

            # Validate required fields
            required_fields = ['title', 'description',
                               'due_date', 'amount', 'project_id']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required'
                    }, 400

            project_id = data['project_id']

            # Verify project exists and user owns it
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }, 404

            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to create milestones for this project'
                }, 403

            # Parse due date
            try:
                due_date = datetime.strptime(
                    data['due_date'], '%Y-%m-%d').date()
            except ValueError:
                return {
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }, 400

            # Create milestone
            milestone = Milestone(
                project_id=project_id,
                title=data['title'],
                description=data['description'],
                due_date=due_date,
                amount=data['amount'],
                status='pending'
            )

            db.session.add(milestone)
            db.session.commit()

            return {
                'success': True,
                'data': milestone.to_dict(),
                'message': 'Milestone created successfully'
            }, 201

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error creating milestone: {str(e)}'
            }, 400


@api.route('/project/<int:project_id>')
class ProjectMilestones(Resource):
    @api.doc(security='Bearer Auth', params={
        'page': 'Page number',
        'per_page': 'Items per page'
    })
    @api.response(200, 'Success')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def get(self, project_id):
        """Get all milestones for a project"""
        try:
            current_user_id = get_jwt_identity()

            # Verify project exists and user has access
            project = Project.query.get_or_404(project_id)

            if project.client_id != current_user_id and project.freelancer_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to view milestones for this project'
                }, 403

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            milestones = Milestone.query.filter_by(project_id=project_id)\
                .order_by(Milestone.due_date.asc())\
                .paginate(page=page, per_page=per_page, error_out=False)

            return {
                'success': True,
                'data': [milestone.to_dict() for milestone in milestones.items],
                'pagination': {
                    'page': milestones.page,
                    'per_page': milestones.per_page,
                    'total': milestones.total,
                    'pages': milestones.pages
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching milestones: {str(e)}'
            }, 500


@api.route('/<int:milestone_id>')
class MilestoneResource(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(404, 'Milestone not found')
    @jwt_required()
    def get(self, milestone_id):
        """Get a specific milestone"""
        try:
            current_user_id = get_jwt_identity()
            milestone = Milestone.query.get_or_404(milestone_id)

            # Verify user has access to the project
            project = Project.query.get(milestone.project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }, 404

            if project.client_id != current_user_id and project.freelancer_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to view this milestone'
                }, 403

            return {
                'success': True,
                'data': milestone.to_dict()
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching milestone: {str(e)}'
            }, 500

    @api.doc(security='Bearer Auth')
    @api.expect(milestone_update_model)
    @api.response(200, 'Milestone updated successfully')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def put(self, milestone_id):
        """Update a milestone"""
        try:
            current_user_id = get_jwt_identity()
            milestone = Milestone.query.get_or_404(milestone_id)

            # Verify user owns the project
            project = Project.query.get(milestone.project_id)
            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to update this milestone'
                }, 403

            data = request.get_json()

            # Update fields if provided
            if 'title' in data:
                milestone.title = data['title']
            if 'description' in data:
                milestone.description = data['description']
            if 'due_date' in data:
                try:
                    milestone.due_date = datetime.strptime(
                        data['due_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {
                        'success': False,
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }, 400
            if 'amount' in data:
                milestone.amount = data['amount']
            if 'status' in data:
                milestone.status = data['status']

            db.session.commit()

            return {
                'success': True,
                'data': milestone.to_dict(),
                'message': 'Milestone updated successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error updating milestone: {str(e)}'
            }, 400

    @api.doc(security='Bearer Auth')
    @api.response(200, 'Milestone deleted successfully')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def delete(self, milestone_id):
        """Delete a milestone"""
        try:
            current_user_id = get_jwt_identity()
            milestone = Milestone.query.get_or_404(milestone_id)

            # Verify user owns the project
            project = Project.query.get(milestone.project_id)
            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to delete this milestone'
                }, 403

            db.session.delete(milestone)
            db.session.commit()

            return {
                'success': True,
                'message': 'Milestone deleted successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error deleting milestone: {str(e)}'
            }, 400


@api.route('/<int:milestone_id>/approve')
class ApproveMilestone(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Milestone approved successfully')
    @api.response(400, 'Cannot approve milestone')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def put(self, milestone_id):
        """Approve a milestone (client action)"""
        try:
            current_user_id = get_jwt_identity()
            milestone = Milestone.query.get_or_404(milestone_id)

            # Verify user owns the project
            project = Project.query.get(milestone.project_id)
            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to approve this milestone'
                }, 403

            # Check if milestone can be approved
            if milestone.status != 'submitted':
                return {
                    'success': False,
                    'message': 'Can only approve submitted milestones'
                }, 400

            milestone.status = 'approved'
            db.session.commit()

            return {
                'success': True,
                'data': milestone.to_dict(),
                'message': 'Milestone approved successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error approving milestone: {str(e)}'
            }, 400


@api.route('/<int:milestone_id>/reject')
class RejectMilestone(Resource):
    @api.doc(security='Bearer Auth')
    @api.expect(api.model('RejectMilestone', {
        'feedback': fields.String(required=True, description='Rejection reason')
    }))
    @api.response(200, 'Milestone rejected successfully')
    @api.response(400, 'Cannot reject milestone')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def put(self, milestone_id):
        """Reject a milestone with feedback"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            milestone = Milestone.query.get_or_404(milestone_id)

            # Verify user owns the project
            project = Project.query.get(milestone.project_id)
            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to reject this milestone'
                }, 403

            if not data.get('feedback'):
                return {
                    'success': False,
                    'message': 'Feedback is required when rejecting a milestone'
                }, 400

            # Check if milestone can be rejected
            if milestone.status != 'submitted':
                return {
                    'success': False,
                    'message': 'Can only reject submitted milestones'
                }, 400

            milestone.status = 'rejected'
            # You might want to store feedback in a separate field or model
            db.session.commit()

            return {
                'success': True,
                'data': milestone.to_dict(),
                'message': 'Milestone rejected with feedback'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error rejecting milestone: {str(e)}'
            }, 400
