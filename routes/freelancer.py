from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Application, TimeEntry, Deliverable, Job, FreelancerProfile
from datetime import datetime, timezone
from http import HTTPStatus
from middlewares.auth_middleware import role_required
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_routes(ns):
    """Register routes for the Freelance namespace"""
    # Define input/output models
    application_model = ns.model('Application', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'freelancer_id': fields.Integer(readonly=True, description='Freelancer ID'),
        'cover_letter': fields.String(description='Cover letter'),
        'proposed_rate': fields.Float(description='Proposed hourly rate'),
        'status': fields.String(enum=['pending', 'accepted', 'rejected'], readonly=True),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True)
    })

    time_entry_model = ns.model('TimeEntry', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'freelancer_id': fields.Integer(readonly=True, description='Freelancer ID'),
        'hours_worked': fields.Float(required=True, description='Hours worked'),
        'date': fields.Date(required=True, description='Date of work'),
        'description': fields.String(description='Work description'),
        'created_at': fields.DateTime(readonly=True)
    })

    deliverable_model = ns.model('Deliverable', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'freelancer_id': fields.Integer(readonly=True, description='Freelancer ID'),
        'title': fields.String(required=True, description='Deliverable title'),
        'file_url': fields.String(required=True, description='URL to deliverable file'),
        'status': fields.String(enum=['submitted', 'reviewed', 'accepted', 'rejected'], readonly=True),
        'submitted_at': fields.DateTime(readonly=True)
    })

    # Application Management Endpoints
    @ns.route('/applications')
    class ApplicationList(Resource):
        @ns.expect(application_model)
        @ns.marshal_with(application_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
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

            # Validate proposed_rate against FreelancerProfile.hourly_rate
            profile = FreelancerProfile.query.filter_by(user_id=freelancer_id).first()
            if not profile:
                logger.error(f"Freelancer {freelancer_id} has no profile")
                return {'message': 'Freelancer profile not found'}, HTTPStatus.BAD_REQUEST
            if data.get('proposed_rate') and profile.hourly_rate and data['proposed_rate'] < float(profile.hourly_rate):
                logger.error(f"Proposed rate {data['proposed_rate']} below profile rate {profile.hourly_rate}")
                return {'message': 'Proposed rate cannot be below your profile hourly rate'}, HTTPStatus.BAD_REQUEST

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
        @role_required('freelancer')
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
        @role_required('freelancer')
        def get(self, id):
            """Get a specific application"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
            if not application:
                logger.error(f"Application {id} not found for freelancer {freelancer_id}")
                return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
            return application, HTTPStatus.OK

        @ns.expect(application_model)
        @ns.marshal_with(application_model)
        @jwt_required()
        @role_required('freelancer')
        def put(self, id):
            """Update a pending application (cover_letter and proposed_rate only)"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
            if not application:
                logger.error(f"Application {id} not found for freelancer {freelancer_id}")
                return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
            if application.status != 'pending':
                logger.error(f"Freelancer {freelancer_id} attempted to update non-pending application {id}")
                return {'message': 'Cannot update non-pending application'}, HTTPStatus.BAD_REQUEST

            data = request.get_json()
            # Validate proposed_rate against FreelancerProfile.hourly_rate
            profile = FreelancerProfile.query.filter_by(user_id=freelancer_id).first()
            if not profile:
                logger.error(f"Freelancer {freelancer_id} has no profile")
                return {'message': 'Freelancer profile not found'}, HTTPStatus.BAD_REQUEST
            if data.get('proposed_rate') and profile.hourly_rate and data['proposed_rate'] < float(profile.hourly_rate):
                logger.error(f"Proposed rate {data['proposed_rate']} below profile rate {profile.hourly_rate}")
                return {'message': 'Proposed rate cannot be below your profile hourly rate'}, HTTPStatus.BAD_REQUEST

            application.cover_letter = data.get('cover_letter', application.cover_letter)
            application.proposed_rate = data.get('proposed_rate', application.proposed_rate)
            application.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Application {id} updated by freelancer {freelancer_id}")
            return application, HTTPStatus.OK

        @jwt_required()
        @role_required('freelancer')
        def delete(self, id):
            """Delete a pending application"""
            freelancer_id = get_jwt_identity()
            application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
            if not application:
                logger.error(f"Application {id} not found for freelancer {freelancer_id}")
                return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
            if application.status != 'pending':
                logger.error(f"Freelancer {freelancer_id} attempted to delete non-pending application {id}")
                return {'message': 'Cannot delete non-pending application'}, HTTPStatus.BAD_REQUEST
            db.session.delete(application)
            db.session.commit()
            logger.info(f"Application {id} deleted by freelancer {freelancer_id}")
            return {'message': 'Application deleted'}, HTTPStatus.NO_CONTENT

    # Time Tracking Endpoints
    @ns.route('/time-entries')
    class TimeEntryList(Resource):
        @ns.expect(time_entry_model)
        @ns.marshal_with(time_entry_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Create a new time entry"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()
            logger.info(f"Freelancer {freelancer_id} creating time entry for job {data['job_id']}")

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=data['job_id'], freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} not assigned to job {data['job_id']}")
                return {'message': 'Job not found or not assigned to you'}, HTTPStatus.BAD_REQUEST

            # Validate hours_worked
            if data['hours_worked'] <= 0:
                logger.error(f"Invalid hours_worked {data['hours_worked']} for freelancer {freelancer_id}")
                return {'message': 'Hours worked must be positive'}, HTTPStatus.BAD_REQUEST

            time_entry = TimeEntry(
                job_id=data['job_id'],
                freelancer_id=freelancer_id,
                hours_worked=data['hours_worked'],
                date=data['date'],
                description=data.get('description'),
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(time_entry)
            db.session.commit()
            logger.info(f"Time entry {time_entry.id} created for freelancer {freelancer_id}")
            return time_entry, HTTPStatus.CREATED

        @ns.marshal_list_with(time_entry_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def get(self):
            """List all time entries for the authenticated freelancer with pagination"""
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            time_entries = TimeEntry.query.filter_by(freelancer_id=freelancer_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(time_entries.items)} time entries")
            return time_entries.items, HTTPStatus.OK

    # Deliverable Submission Endpoints
    @ns.route('/deliverables')
    class DeliverableList(Resource):
        @ns.expect(deliverable_model)
        @ns.marshal_with(deliverable_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Submit a new deliverable"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()
            logger.info(f"Freelancer {freelancer_id} submitting deliverable for job {data['job_id']}")

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=data['job_id'], freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} not assigned to job {data['job_id']}")
                return {'message': 'Job not found or not assigned to you'}, HTTPStatus.BAD_REQUEST

            # Validate file_url (basic check, adjust for your storage service)
            if not data['file_url'].startswith(('http://', 'https://', 's3://')):
                logger.error(f"Invalid file_url {data['file_url']} for freelancer {freelancer_id}")
                return {'message': 'Invalid file URL'}, HTTPStatus.BAD_REQUEST

            deliverable = Deliverable(
                job_id=data['job_id'],
                freelancer_id=freelancer_id,
                title=data['title'],
                file_url=data['file_url'],
                status='submitted',
                submitted_at=datetime.now(timezone.utc)
            )
            db.session.add(deliverable)
            db.session.commit()
            logger.info(f"Deliverable {deliverable.id} submitted by freelancer {freelancer_id}")
            return deliverable, HTTPStatus.CREATED

        @ns.marshal_list_with(deliverable_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def get(self):
            """List all deliverables for the authenticated freelancer with pagination"""
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            deliverables = Deliverable.query.filter_by(freelancer_id=freelancer_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(deliverables.items)} deliverables")
            return deliverables.items, HTTPStatus.OK