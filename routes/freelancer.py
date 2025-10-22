

from flask_restx import Namespace, Resource, fields
from flask import request
from extensions import db
from models import Application, TimeEntry, Deliverable, Invoice, Payment
from datetime import datetime, timezone

# -----------------------------
# Namespace
# -----------------------------
freelancer_ns = Namespace('freelancer', description='Freelancer APIs')

# -----------------------------
# Models for RESTX
# -----------------------------
application_model = freelancer_ns.model('Application', {
    'id': fields.Integer(readonly=True),
    'title': fields.String(required=True),
    'description': fields.String(required=True),
    'status': fields.String(description='Application status')
})

time_entry_model = freelancer_ns.model('TimeEntry', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'hours': fields.Float(required=True),
    'description': fields.String,
    'date': fields.DateTime
})

deliverable_model = freelancer_ns.model('Deliverable', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'title': fields.String(required=True),
    'file_url': fields.String,
    'submitted_at': fields.DateTime
})

invoice_model = freelancer_ns.model('Invoice', {
    'id': fields.Integer(readonly=True),
    'project_id': fields.Integer(required=True),
    'amount': fields.Float(required=True),
    'status': fields.String,
    'created_at': fields.DateTime
})

payment_model = freelancer_ns.model('Payment', {
    'id': fields.Integer(readonly=True),
    'invoice_id': fields.Integer(required=True),
    'amount': fields.Float(required=True),
    'status': fields.String,
    'created_at': fields.DateTime
})

# -----------------------------
# Applications Endpoints
# -----------------------------
@freelancer_ns.route('/applications')
class ApplicationList(Resource):
    @freelancer_ns.marshal_list_with(application_model)
    def get(self):
        return Application.query.all(), 200

    @freelancer_ns.expect(application_model, validate=True)
    @freelancer_ns.marshal_with(application_model, code=201)
    def post(self):
        data = request.json
        app = Application(
            title=data['title'],
            description=data['description'],
            status=data.get('status', 'pending')
        )
        db.session.add(app)
        db.session.commit()
        return app, 201

@freelancer_ns.route('/applications/<int:id>')
class ApplicationDetail(Resource):
    @freelancer_ns.marshal_with(application_model)
    def get(self, id):
        return Application.query.get_or_404(id), 200

# -----------------------------
# Time Entries Endpoints
# -----------------------------
@freelancer_ns.route('/time-entries')
class TimeEntryList(Resource):
    @freelancer_ns.marshal_list_with(time_entry_model)
    def get(self):
        return TimeEntry.query.all(), 200

    @freelancer_ns.expect(time_entry_model, validate=True)
    @freelancer_ns.marshal_with(time_entry_model, code=201)
    def post(self):
        data = request.json
        entry = TimeEntry(
            project_id=data['project_id'],
            hours=data['hours'],
            description=data.get('description'),
            date=datetime.now(timezone.utc)
        )
        db.session.add(entry)
        db.session.commit()
        return entry, 201

@freelancer_ns.route('/time-entries/<int:id>')
class TimeEntryDetail(Resource):
    @freelancer_ns.marshal_with(time_entry_model)
    def get(self, id):
        return TimeEntry.query.get_or_404(id), 200

# -----------------------------
# Deliverables Endpoints
# -----------------------------
@freelancer_ns.route('/deliverables')
class DeliverableList(Resource):
    @freelancer_ns.marshal_list_with(deliverable_model)
    def get(self):
        return Deliverable.query.all(), 200

    @freelancer_ns.expect(deliverable_model, validate=True)
    @freelancer_ns.marshal_with(deliverable_model, code=201)
    def post(self):
        data = request.json
        deliverable = Deliverable(
            project_id=data['project_id'],
            title=data['title'],
            file_url=data.get('file_url'),
            submitted_at=datetime.now(timezone.utc)
        )
        db.session.add(deliverable)
        db.session.commit()
        return deliverable, 201

@freelancer_ns.route('/deliverables/<int:id>')
class DeliverableDetail(Resource):
    @freelancer_ns.marshal_with(deliverable_model)
    def get(self, id):
        return Deliverable.query.get_or_404(id), 200

# -----------------------------
# Invoices Endpoints
# -----------------------------
@freelancer_ns.route('/invoices')
class InvoiceList(Resource):
    @freelancer_ns.marshal_list_with(invoice_model)
    def get(self):
        return Invoice.query.all(), 200

    @freelancer_ns.expect(invoice_model, validate=True)
    @freelancer_ns.marshal_with(invoice_model, code=201)
    def post(self):
        data = request.json
        invoice = Invoice(
            project_id=data['project_id'],
            amount=data['amount'],
            status=data.get('status', 'pending'),
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice, 201

@freelancer_ns.route('/invoices/<int:id>')
class InvoiceDetail(Resource):
    @freelancer_ns.marshal_with(invoice_model)
    def get(self, id):
        return Invoice.query.get_or_404(id), 200

# -----------------------------
# Payments Endpoints
# -----------------------------
@freelancer_ns.route('/payments')
class PaymentList(Resource):
    @freelancer_ns.marshal_list_with(payment_model)
    def get(self):
        return Payment.query.all(), 200

    @freelancer_ns.expect(payment_model, validate=True)
    @freelancer_ns.marshal_with(payment_model, code=201)
    def post(self):
        data = request.json
        payment = Payment(
            invoice_id=data['invoice_id'],
            amount=data['amount'],
            status=data['status'],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(payment)
        db.session.commit()
        return payment, 201

@freelancer_ns.route('/payments/<int:id>')
class PaymentDetail(Resource):
    @freelancer_ns.marshal_with(payment_model)
    def get(self, id):
        return Payment.query.get_or_404(id), 200
