from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import Application, TimeEntry, Deliverable, Job, FreelancerProfile
from datetime import datetime, timezone
from http import HTTPStatus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_routes(ns):
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

    @ns.route('/applications')
    class ApplicationList(Resource):
        @ns.expect(application_model)
        @ns.marshal_with(application_model, envelope='data')
        @jwt_required()
        def post(self):
            """Create a new job application"""
            claims = get_jwt()
            if claims.get('role') != 'freelancer':
                logger.error(f"User {get_jwt_identity()} attempted access with role {claims.get('role')}")
                return {'message': 'Only freelancers are authorized'}, HTTPStatus.FORBIDDEN
            data = request.get_json()
            freelancer_id = get_jwt_identity()
            job = Job.query.filter_by(id=data['job_id'], status='open').first()
            if not job:
                logger.error(f"Job {data['job_id']} not found or not open")
                return {'message': 'Job not found or not open'}, HTTPStatus.BAD_REQUEST
            if Application.query.filter_by(job_id=data['job_id'], freelancer_id=freelancer_id).first():
                logger.error(f"Freelancer {freelancer_id} already applied to job {data['job_id']}")
                return {'message': 'You have already applied to this job'}, HTTPStatus.BAD_REQUEST
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
        def get(self):
            """List all applications for the authenticated freelancer with pagination"""
            claims = get_jwt()
            if claims.get('role') != 'freelancer':
                logger.error(f"User {get_jwt_identity()} attempted access with role {claims.get('role')}")
                return {'message': 'Only freelancers are authorized'}, HTTPStatus.FORBIDDEN
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            applications = Application.query.filter_by(freelancer_id=freelancer_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(applications.items)} applications")
            return applications.items, HTTPStatus.OK
    # ... apply similar changes to ApplicationDetail, TimeEntryList, DeliverableList ...