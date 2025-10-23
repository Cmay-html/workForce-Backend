from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Invoice, Application, TimeEntry, FreelancerProfile
from datetime import datetime, timezone
from http import HTTPStatus
from middlewares.auth_middleware import role_required
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_routes(ns):
    invoice_model = ns.model('Invoice', {
        'job_id': fields.Integer(required=True, description='Job ID'),
        'amount': fields.Float(required=True, min=0, description='Invoice amount'),
        'due_date': fields.Date(required=True, description='Due date'),
        'status': fields.String(enum=['pending', 'paid', 'overdue'], readonly=True),
        'created_at': fields.DateTime(readonly=True)
    })

    @ns.route('/invoices')
    class InvoiceList(Resource):
        @ns.expect(invoice_model)
        @ns.marshal_with(invoice_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def post(self):
            """Create a new invoice for an assigned job"""
            data = request.get_json()
            freelancer_id = get_jwt_identity()

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=data['job_id'], freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} attempted to create invoice for unassigned job {data['job_id']}")
                return {'message': 'Job not found or not assigned to you'}, HTTPStatus.BAD_REQUEST

            # Validate due_date is in the future
            due_date = data['due_date']
            if due_date <= datetime.now(timezone.utc).date():
                logger.error(f"Invalid due_date {due_date} for invoice by freelancer {freelancer_id}")
                return {'message': 'Due date must be in the future'}, HTTPStatus.BAD_REQUEST

            invoice = Invoice(
                job_id=data['job_id'],
                freelancer_id=freelancer_id,
                amount=data['amount'],
                due_date=due_date,
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(invoice)
            db.session.commit()
            logger.info(f"Invoice created for job {data['job_id']} by freelancer {freelancer_id}")
            return invoice, HTTPStatus.CREATED

        @ns.marshal_list_with(invoice_model, envelope='data')
        @jwt_required()
        @role_required('freelancer')
        def get(self):
            """List all invoices for the authenticated freelancer with pagination"""
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(invoices.items)} invoices")
            return invoices.items, HTTPStatus.OK

    @ns.route('/invoices/calculate/<int:job_id>')
    class InvoiceCalculate(Resource):
        @jwt_required()
        @role_required('freelancer')
        def get(self, job_id):
            """Calculate invoice amount based on time entries and hourly rate"""
            freelancer_id = get_jwt_identity()

            # Validate job exists and freelancer is assigned
            application = Application.query.filter_by(
                job_id=job_id, freelancer_id=freelancer_id, status='accepted'
            ).first()
            if not application:
                logger.error(f"Freelancer {freelancer_id} attempted to calculate invoice for unassigned job {job_id}")
                return {'message': 'Job not found or not assigned'}, HTTPStatus.BAD_REQUEST

            # Get hourly rate
            profile = FreelancerProfile.query.filter_by(user_id=freelancer_id).first()
            if not profile or not profile.hourly_rate:
                logger.error(f"Freelancer {freelancer_id} has no hourly rate set")
                return {'message': 'Hourly rate not set in profile'}, HTTPStatus.BAD_REQUEST

            # Calculate total hours
            time_entries = TimeEntry.query.filter_by(job_id=job_id, freelancer_id=freelancer_id).all()
            total_hours = sum(entry.hours_worked for entry in time_entries)
            amount = total_hours * float(profile.hourly_rate)

            logger.info(f"Calculated invoice for job {job_id}: {total_hours} hours, ${amount}")
            return {
                'job_id': job_id,
                'total_hours': total_hours,
                'hourly_rate': float(profile.hourly_rate),
                'amount': amount
            }, HTTPStatus.OK