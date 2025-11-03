from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models import TimeEntry, Application
from datetime import datetime, timezone
from http import HTTPStatus
from middlewares.auth_middleware import role_required
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_routes(ns):
    time_entry_model = ns.model('TimeEntry', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'hours_worked': fields.Float(required=True, min=0, description='Hours worked'),
        'date': fields.Date(required=True, description='Date of work'),
        'description': fields.String(description='Work description'),
        'created_at': fields.DateTime(readonly=True)
    })

    @ns.route('/time-entries')
    class TimeEntryList(Resource):
        @ns.expect(time_entry_model)
        @ns.marshal_with(time_entry_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Create a new time entry for an assigned job"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=data['job_id'], freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} attempted to log time for unassigned job {data['job_id']}")
                return {'message': 'Job not found or not assigned to you'}, HTTPStatus.BAD_REQUEST

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
            logger.info(f"Time entry created for job {data['job_id']} by freelancer {freelancer_id}")
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