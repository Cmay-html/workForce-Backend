from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models import Payment, Invoice
from http import HTTPStatus
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_routes(ns):
    payment_model = ns.model('Payment', {
        'invoice_id': fields.Integer(readonly=True, description='Invoice ID'),
        'amount': fields.Float(readonly=True, description='Payment amount'),
        'payment_date': fields.Date(readonly=True, description='Payment date'),
        'payment_method': fields.String(readonly=True, description='Payment method')
    })

    @ns.route('/payments')
    class PaymentList(Resource):
        @ns.marshal_list_with(payment_model, envelope='data')
        @jwt_required()
        def get(self):
            """List all payments for the authenticated freelancer with pagination"""
            claims = get_jwt()
            if claims.get('role') != 'freelancer':
                logger.error(f"User {get_jwt_identity()} attempted access with role {claims.get('role')}")
                return {'message': 'Only freelancers are authorized'}, HTTPStatus.FORBIDDEN
            freelancer_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
            invoice_ids = [invoice.id for invoice in invoices]
            payments = Payment.query.filter(Payment.invoice_id.in_(invoice_ids)).paginate(
                page=page, per_page=per_page, error_out=False
            )
            logger.info(f"Freelancer {freelancer_id} retrieved {len(payments.items)} payments")
            return payments.items, HTTPStatus.OK

    @ns.route('/payments/<int:id>')
    class PaymentDetail(Resource):
        @ns.marshal_with(payment_model)
        @jwt_required()
        def get(self, id):
            """Get a specific payment"""
            claims = get_jwt()
            if claims.get('role') != 'freelancer':
                logger.error(f"User {get_jwt_identity()} attempted access with role {claims.get('role')}")
                return {'message': 'Only freelancers are authorized'}, HTTPStatus.FORBIDDEN
            freelancer_id = get_jwt_identity()
            invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
            invoice_ids = [invoice.id for invoice in invoices]
            payment = Payment.query.filter(Payment.id == id, Payment.invoice_id.in_(invoice_ids)).first()
            if not payment:
                logger.error(f"Payment {id} not found for freelancer {freelancer_id}")
                return {'message': 'Payment not found'}, HTTPStatus.NOT_FOUND
            return payment, HTTPStatus.OK