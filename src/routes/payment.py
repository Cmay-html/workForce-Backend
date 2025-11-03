import os
from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, get_jwt
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from models import Payment, ClientProfile, Invoice
from ..extensions import db
from http import HTTPStatus
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create namespace for client payments
ns = Namespace('client/payments', description='Client Payment Operations')

# Role-based JWT Authentication Decorator
def require_role(role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != role:
                logger.error(f"User {get_jwt_identity()} attempted access with role {claims.get('role')}")
                return {'message': f'Only {role}s are authorized'}, HTTPStatus.FORBIDDEN
            user_email = get_jwt_identity()
            user = ClientProfile.query.filter_by(email=user_email).first()
            if not user:
                logger.error(f"Client profile not found for email {user_email}")
                return {'message': 'Client profile not found'}, HTTPStatus.NOT_FOUND
            request.user = user
            return f(*args, **kwargs)
        return decorated
    return decorator

# Payment initialization endpoint
@ns.route('/initiate')
class PaymentInitiate(Resource):
    payment_model = ns.model('Payment', {
        'amount': fields.Float(required=True, description='Payment amount'),
        'currency': fields.String(required=True, description='Currency', default='NGN'),
        'customer_email': fields.String(required=True, description='Customer email'),
        'customer_name': fields.String(required=True, description='Customer name'),
        'invoice_id': fields.Integer(required=True, description='Invoice ID')
    })

    @ns.expect(payment_model)
    @require_role('client')
    def post(self):
        """Initiate a payment for an invoice"""
        data = request.get_json()
        amount = data.get('amount')
        currency = data.get('currency')
        customer_email = data.get('customer_email')
        customer_name = data.get('customer_name')
        invoice_id = data.get('invoice_id')

        # Validate inputs
        if amount <= 0:
            logger.error(f"Invalid amount {amount} for payment by client {get_jwt_identity()}")
            return {'message': 'Amount must be positive'}, HTTPStatus.BAD_REQUEST
        if currency not in ['NGN', 'USD']:
            logger.error(f"Unsupported currency {currency} for payment by client {get_jwt_identity()}")
            return {'message': 'Unsupported currency'}, HTTPStatus.BAD_REQUEST

        # Get client from JWT
        client = request.user
        invoice = Invoice.query.get_or_404(invoice_id)
        if invoice.client_id != client.id:
            logger.error(f"Client {client.id} attempted to pay unauthorized invoice {invoice_id}")
            return {'message': 'Unauthorized invoice'}, HTTPStatus.FORBIDDEN

        # Generate unique transaction reference
        tx_ref = f"TX-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{client.id}"

        try:
            # Create pending payment record
            payment = Payment(
                invoice_id=invoice_id,
                client_id=client.id,
                amount=amount,
                transaction_id=tx_ref,
                status='pending',
                payment_date=datetime.now(timezone.utc).date()
            )
            db.session.add(payment)
            db.session.commit()
            logger.info(f"Payment {payment.id} initiated for invoice {invoice_id} by client {client.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create payment for invoice {invoice_id}: {str(e)}")
            return {'message': f'Failed to create payment: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR

        # Mock payment processing (replace with actual payment gateway logic, e.g., Paystack)
        try:
            payment_url = f"https://your-app.com/mock-payment?tx_ref={tx_ref}"
            return {
                'payment_url': payment_url,
                'tx_ref': tx_ref,
                'payment_id': payment.id
            }, HTTPStatus.OK
        except Exception as e:
            logger.error(f"Failed to initiate payment for tx_ref {tx_ref}: {str(e)}")
            return {'message': f'Failed to initiate payment: {str(e)}'}, HTTPStatus.BAD_REQUEST

# Payment verification endpoint
@ns.route('/verify/<string:tx_ref>')
class PaymentVerify(Resource):
    @require_role('client')
    def get(self, tx_ref):
        """Verify a payment by transaction reference"""
        client = request.user
        payment = Payment.query.filter_by(transaction_id=tx_ref, client_id=client.id).first()
        if not payment:
            logger.error(f"Payment with tx_ref {tx_ref} not found for client {client.id}")
            return {'message': 'Payment not found or unauthorized'}, HTTPStatus.NOT_FOUND

        # Mock verification (replace with actual payment gateway verification)
        try:
            if payment.status == 'pending':
                payment.status = 'completed'
                payment.paid_at = datetime.now(timezone.utc)
                invoice = Invoice.query.get(payment.invoice_id)
                if invoice:
                    invoice.status = 'paid'
                db.session.commit()
                logger.info(f"Payment {payment.id} verified for client {client.id}")
                return {
                    'message': 'Payment verified successfully',
                    'data': {
                        'transaction_id': tx_ref,
                        'status': payment.status,
                        'amount': float(payment.amount),
                        'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
                    }
                }, HTTPStatus.OK
            logger.error(f"Payment {payment.id} not pending for client {client.id}")
            return {'message': 'Payment not successful'}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            logger.error(f"Failed to verify payment {tx_ref}: {str(e)}")
            return {'message': f'Failed to verify payment: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR

# Webhook endpoint for payment notifications
@ns.route('/webhook')
class PaymentWebhook(Resource):
    webhook_model = ns.model('Webhook', {
        'txRef': fields.String(required=True, description='Transaction reference'),
        'status': fields.String(required=True, description='Payment status')
    })

    @ns.expect(webhook_model)
    def post(self):
        """Handle payment webhook notifications"""
        data = request.get_json()
        tx_ref = data.get('txRef')
        status = data.get('status')

        if status != 'successful':
            logger.info(f"Webhook skipped for tx_ref {tx_ref}: status {status}")
            return {'message': 'Webhook processing skipped: Payment not successful'}, HTTPStatus.OK

        try:
            payment = Payment.query.filter_by(transaction_id=tx_ref).first()
            if not payment:
                logger.error(f"Payment with tx_ref {tx_ref} not found")
                return {'message': 'Payment not found'}, HTTPStatus.NOT_FOUND
            payment.status = 'completed'
            payment.paid_at = datetime.now(timezone.utc)
            invoice = Invoice.query.get(payment.invoice_id)
            if invoice:
                invoice.status = 'paid'
            db.session.commit()
            logger.info(f"Webhook processed for payment {payment.id}, tx_ref {tx_ref}")
            return {'message': 'Webhook processed successfully'}, HTTPStatus.OK
        except Exception as e:
            db.session.rollback()
            logger.error(f"Webhook processing failed for tx_ref {tx_ref}: {str(e)}")
            return {'message': f'Webhook processing failed: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR

# Payment list endpoint
@ns.route('')
class PaymentList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, default=1, help='Page number')
    parser.add_argument('per_page', type=int, default=10, help='Items per page')

    @ns.expect(parser)
    @require_role('client')
    def get(self):
        """List all payments for the authenticated client with pagination"""
        args = self.parser.parse_args()
        client = request.user
        page = args['page']
        per_page = args['per_page']
        payments = Payment.query.filter_by(client_id=client.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        logger.info(f"Client {client.id} retrieved {len(payments.items)} payments")
        return {
            'data': [{
                'id': payment.id,
                'invoice_id': payment.invoice_id,
                'amount': float(payment.amount),
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
            } for payment in payments.items],
            'total': payments.total,
            'pages': payments.pages
        }, HTTPStatus.OK

# Payment detail endpoint
@ns.route('/<int:payment_id>')
class PaymentDetail(Resource):
    payment_model = ns.model('PaymentDetail', {
        'id': fields.Integer(readonly=True, description='Payment ID'),
        'invoice_id': fields.Integer(readonly=True, description='Invoice ID'),
        'amount': fields.Float(readonly=True, description='Payment amount'),
        'transaction_id': fields.String(readonly=True, description='Transaction ID'),
        'status': fields.String(readonly=True, description='Payment status'),
        'payment_date': fields.Date(readonly=True, description='Payment date'),
        'paid_at': fields.DateTime(readonly=True, description='Payment confirmation time')
    })

    @ns.marshal_with(payment_model)
    @require_role('client')
    def get(self, payment_id):
        """Get a specific payment"""
        client = request.user
        payment = Payment.query.filter_by(id=payment_id, client_id=client.id).first()
        if not payment:
            logger.error(f"Payment {payment_id} not found for client {client.id}")
            return {'message': 'Payment not found or unauthorized'}, HTTPStatus.NOT_FOUND
        logger.info(f"Client {client.id} retrieved payment {payment_id}")
        return payment, HTTPStatus.OK

# Function to register the namespace with the main API
def register_routes(ns):
    """Register routes for the client payments namespace"""
    pass  # Namespace is already defined above; no additional registration needed