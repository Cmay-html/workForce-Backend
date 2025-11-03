from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Application, Job
from datetime import datetime, timezone
from http import HTTPStatus
# from auth_middleware import role_required  # Commented out as middleware doesn't exist
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the namespace (imported from __init__.py)
def register_routes(ns):
    # Define the application model
    application_model = ns.model('Application', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'cover_letter': fields.String(description='Cover letter'),
        'proposed_rate': fields.Float(min=0, description='Proposed hourly rate'),
        'status': fields.String(enum=['pending', 'accepted', 'rejected'], readonly=True),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True)
    })

    @ns.route('/applications')
    class ApplicationList(Resource):
        @ns.expect(application_model)
        @ns.marshal_with(application_model, envelope='data')
        @jwt_required()
        # @role_required('freelancer')  # Commented out as middleware doesn't exist
        def post(self):
            """Create a new job application"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()
            logger.info(f"Freelancer {freelancer_id} applying to job {data['job_id']}")

            # Validate job exists and is open
            job = Job.query.filter_by(id=data['job_id'], status='open').first()
            if not job:
                logger.error(f"Job {data['job_id']} not found or not open")
                return {'message': 'Job not found or not open'}, HTTPStatus.BAD_REQUEST

            # Check for duplicate application
            if Application.query.filter_by(job_id=data['job_id'], freelancer_id=freelancer_id).first():
                logger.error(f"Freelancer {freelancer_id} already applied to job {data['job_id']}")
                return {'message': 'You have already applied to this job'}, HTTPStatus.BAD_REQUEST

            application = Application(
                job_id=data['job_id'],
                freelancer_id=freelancer_id,
                cover_letter=data.get('cover_letter'),
                proposed_rate=data.get('proposed_rate'),
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(application)
            db.session.commit()
            logger.info(f"Application {application.id} created")
            return application, HTTPStatus.CREATED

        @ns.marshal_list_with(application_model, envelope='data')
        @jwt_required()
        # @role_required('freelancer')  # Commented out as middleware doesn't exist
        def get(self):
            """List all applications for the authenticated freelancer with pagination"""
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            applications = Application.query.filter_by(freelancer_id=freelancer_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(applications.items)} applications")
            return applications.items, HTTPStatus.OK

    @ns.route('/applications/<int:id>')
    class ApplicationDetail(Resource):
        @ns.marshal_with(application_model)
        @jwt_required()
        # @role_required('freelancer')  # Commented out as middleware doesn't exist
        def get(self, id):
            """Get a specific application"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first_or_404()
            return application, HTTPStatus.OK

        @ns.expect(application_model)
        @ns.marshal_with(application_model)
        @jwt_required()
        # @role_required('freelancer')  # Commented out as middleware doesn't exist
        def put(self, id):
            """Update a pending application (cover_letter and proposed_rate only)"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first_or_404()
            if application.status != 'pending':
                logger.error(f"Freelancer {freelancer_id} attempted to update non-pending application {id}")
                return {'message': 'Cannot update non-pending application'}, HTTPStatus.BAD_REQUEST
            data = request.get_json()
            application.cover_letter = data.get('cover_letter', application.cover_letter)
            application.proposed_rate = data.get('proposed_rate', application.proposed_rate)
            application.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Application {id} updated by freelancer {freelancer_id}")
            return application, HTTPStatus.OK

        @jwt_required()
        # @role_required('freelancer')  # Commented out as middleware doesn't exist
        def delete(self, id):
            """Delete a pending application"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first_or_404()
            if application.status != 'pending':
                logger.error(f"Freelancer {freelancer_id} attempted to delete non-pending application {id}")
                return {'message': 'Cannot delete non-pending application'}, HTTPStatus.BAD_REQUEST
            db.session.delete(application)
            db.session.commit()
            logger.info(f"Application {id} deleted by freelancer {freelancer_id}")
            return {'message': 'Application deleted'}, HTTPStatus.NO_CONTENT