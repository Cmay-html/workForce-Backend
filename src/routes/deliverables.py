from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models import Deliverable, Application
from datetime import datetime, timezone
from http import HTTPStatus
from middlewares.auth_middleware import role_required
from utils.validators import is_valid_url
from werkzeug.utils import secure_filename
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_FOLDER = 'uploads/deliverables'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def register_routes(ns):
    deliverable_model = ns.model('Deliverable', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'title': fields.String(required=True, description='Deliverable title'),
        'file_url': fields.String(readonly=True, description='URL to deliverable file'),
        'status': fields.String(enum=['submitted', 'reviewed', 'accepted', 'rejected'], readonly=True),
        'submitted_at': fields.DateTime(readonly=True)
    })

    @ns.route('/deliverables')
    class DeliverableList(Resource):
        @ns.expect(deliverable_model)
        @ns.marshal_with(deliverable_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Submit a new deliverable (URL-based)"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=data['job_id'], freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} attempted to submit deliverable for unassigned job {data['job_id']}")
                return {'message': 'Job not found or not assigned to you'}, HTTPStatus.BAD_REQUEST

            # Validate file URL
            if not is_valid_url(data['file_url']):
                logger.error(f"Invalid file URL provided by freelancer {freelancer_id}")
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
            logger.info(f"Deliverable created for job {data['job_id']} by freelancer {freelancer_id}")
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

    @ns.route('/deliverables/upload')
    class DeliverableUpload(Resource):
        @ns.marshal_with(deliverable_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Upload a file for a deliverable"""
            freelancer_id = get_jwt_identity()
            if 'file' not in request.files or 'job_id' not in request.form or 'title' not in request.form:
                logger.error(f"Freelancer {freelancer_id} missing required fields for deliverable upload")
                return {'message': 'File, job_id, and title required'}, HTTPStatus.BAD_REQUEST

            file = request.files['file']
            job_id = request.form['job_id']
            title = request.form['title']

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=job_id, freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} attempted to upload deliverable for unassigned job {job_id}")
                return {'message': 'Job not found or not assigned'}, HTTPStatus.BAD_REQUEST

            # Save file locally
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, f"{freelancer_id}_{job_id}_{filename}")
            file.save(file_path)
            file_url = f"/uploads/deliverables/{freelancer_id}_{job_id}_{filename}"

            deliverable = Deliverable(
                job_id=job_id,
                freelancer_id=freelancer_id,
                title=title,
                file_url=file_url,
                status='submitted',
                submitted_at=datetime.now(timezone.utc)
            )
            db.session.add(deliverable)
            db.session.commit()
            logger.info(f"Deliverable uploaded for job {job_id} by freelancer {freelancer_id}")
            return deliverable, HTTPStatus.CREATED