from flask_restx import Namespace, Resource, fields
from flask import request
from extensions import db
from models import Application, TimeEntry, Deliverable, Invoice, Payment
from datetime import datetime, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus

# Define the Freelance namespace
freelance_ns = Namespace('freelance', description='Freelancer journey operations')

# Define input/output models for validation and Swagger documentation
application_model = freelance_ns.model('Application', {
    'job_id': fields.Integer(required=True, description='Job ID'),
    'freelancer_id': fields.Integer(required=True, description='Freelancer ID'),
    'cover_letter': fields.String(description='Cover letter'),
    'proposed_rate': fields.Float(description='Proposed hourly rate'),
    'status': fields.String(enum=['pending', 'accepted', 'rejected'], description='Application status')
})

time_entry_model = freelance_ns.model('TimeEntry', {
    'job_id': fields.Integer(required=True, description='Job ID'),
    'freelancer_id': fields.Integer(required=True, description='Freelancer ID'),
    'hours_worked': fields.Float(required=True, description='Hours worked'),
    'date': fields.Date(required=True, description='Date of work'),
    'description': fields.String(description='Work description')
})

deliverable_model = freelance_ns.model('Deliverable', {
    'job_id': fields.Integer(required=True, description='Job ID'),
    'freelancer_id': fields.Integer(required=True, description='Freelancer ID'),
    'title': fields.String(required=True, description='Deliverable title'),
    'file_url': fields.String(required=True, description='URL to deliverable file'),
    'status': fields.String(enum=['submitted', 'reviewed', 'accepted', 'rejected'], description='Deliverable status')
})

invoice_model = freelance_ns.model('Invoice', {
    'job_id': fields.Integer(required=True, description='Job ID'),
    'freelancer_id': fields.Integer(required=True, description='Freelancer ID'),
    'amount': fields.Float(required=True, description='Invoice amount'),
    'due_date': fields.Date(required=True, description='Due date'),
    'status': fields.String(enum=['pending', 'paid', 'overdue'], description='Invoice status')
})

payment_model = freelance_ns.model('Payment', {
    'invoice_id': fields.Integer(required=True, description='Invoice ID'),
    'amount': fields.Float(required=True, description='Payment amount'),
    'payment_date': fields.Date(required=True, description='Payment date'),
    'payment_method': fields.String(description='Payment method')
})

# Application Management Endpoints
@freelance_ns.route('/applications')
class ApplicationList(Resource):
    @freelance_ns.expect(application_model)
    @freelance_ns.marshal_with(application_model, envelope='data')
    @jwt_required()
    def post(self):
        """Create a new job application"""
        data = request.get_json()
        freelancer_id = get_jwt_identity()
        
        if data['freelancer_id'] != freelancer_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
            
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
        return application, HTTPStatus.CREATED

    @freelance_ns.marshal_list_with(application_model, envelope='data')
    @jwt_required()
    def get(self):
        """List all applications for the authenticated freelancer"""
        freelancer_id = get_jwt_identity()
        applications = Application.query.filter_by(freelancer_id=freelancer_id).all()
        return applications, HTTPStatus.OK

@freelance_ns.route('/applications/<int:id>')
class ApplicationDetail(Resource):
    @freelance_ns.marshal_with(application_model)
    @jwt_required()
    def get(self, id):
        """Get a specific application"""
        freelancer_id = get_jwt_identity()
        application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
        if not application:
            return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
        return application, HTTPStatus.OK

    @freelance_ns.expect(application_model)
    @freelance_ns.marshal_with(application_model)
    @jwt_required()
    def put(self, id):
        """Update an application"""
        freelancer_id = get_jwt_identity()
        application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
        if not application:
            return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
            
        data = request.get_json()
        application.cover_letter = data.get('cover_letter', application.cover_letter)
        application.proposed_rate = data.get('proposed_rate', application.proposed_rate)
        application.status = data.get('status', application.status)
        application.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return application, HTTPStatus.OK

    @jwt_required()
    def delete(self, id):
        """Delete an application"""
        freelancer_id = get_jwt_identity()
        application = Application.query.filter_by(id=id, freelancer_id=freelancer_id).first()
        if not application:
            return {'message': 'Application not found'}, HTTPStatus.NOT_FOUND
        db.session.delete(application)
        db.session.commit()
        return {'message': 'Application deleted'}, HTTPStatus.NO_CONTENT


# Deliverable Submission Endpoints
@freelance_ns.route('/deliverables')
class DeliverableList(Resource):
    @freelance_ns.expect(deliverable_model)
    @freelance_ns.marshal_with(deliverable_model, envelope='data')
    @jwt_required()
    def post(self):
        """Submit a new deliverable"""
        data = request.get_json()
        freelancer_id = get_jwt_identity()
        
        if data['freelancer_id'] != freelancer_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
            
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
        return deliverable, HTTPStatus.CREATED

    @freelance_ns.marshal_list_with(deliverable_model, envelope='data')
    @jwt_required()
    def get(self):
        """List all deliverables for the authenticated freelancer"""
        freelancer_id = get_jwt_identity()
        deliverables = Deliverable.query.filter_by(freelancer_id=freelancer_id).all()
        return deliverables, HTTPStatus.OK

# Invoice Endpoints
@freelance_ns.route('/invoices')
class InvoiceList(Resource):
    @freelance_ns.expect(invoice_model)
    @freelance_ns.marshal_with(invoice_model, envelope='data')
    @jwt_required()
    def post(self):
        """Create a new invoice"""
        data = request.get_json()
        freelancer_id = get_jwt_identity()
        
        if data['freelancer_id'] != freelancer_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
            
        invoice = Invoice(
            job_id=data['job_id'],
            freelancer_id=freelancer_id,
            amount=data['amount'],
            due_date=data['due_date'],
            status='pending',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice, HTTPStatus.CREATED

    @freelance_ns.marshal_list_with(invoice_model, envelope='data')
    @jwt_required()
    def get(self):
        """List all invoices for the authenticated freelancer"""
        freelancer_id = get_jwt_identity()
        invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
        return invoices, HTTPStatus.OK

# Payment History Endpoints
@freelance_ns.route('/payments')
class PaymentList(Resource):
    @freelance_ns.marshal_list_with(payment_model, envelope='data')
    @jwt_required()
    def get(self):
        """List all payments for the authenticated freelancer"""
        freelancer_id = get_jwt_identity()
        invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
        invoice_ids = [invoice.id for invoice in invoices]
        payments = Payment.query.filter(Payment.invoice_id.in_(invoice_ids)).all()
        return payments, HTTPStatus.OK

@freelance_ns.route('/payments/<int:id>')
class PaymentDetail(Resource):
    @freelance_ns.marshal_with(payment_model)
    @jwt_required()
    def get(self, id):
        """Get a specific payment"""
        freelancer_id = get_jwt_identity()
        invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
        invoice_ids = [invoice.id for invoice in invoices]
        payment = Payment.query.filter_by(id=id, invoice_id=invoice_ids).first()
        if not payment:
            return {'message': 'Payment not found'}, HTTPStatus.NOT_FOUND
        return payment, HTTPStatus.OK