<<<<<<< HEAD
import os
import requests
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from models.payment import Payment
from models.user import User
from extensions import db

# Load environment variables
load_dotenv()
FLUTTERWAVE_SECRET_KEY = os.getenv('FLUTTERWAVE_SECRET_KEY')

# Create namespace for payments
ns = Namespace('payments', description='Payment Operations')

# JWT Authentication Decorator
def require_jwt(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        request.user = {'email': get_jwt_identity()}  # Attach user identity to request
        return f(*args, **kwargs)
    return decorated

# Sample user authentication endpoint (for Flutter app to get JWT)
@ns.route('/auth/login')
class Login(Resource):
    login_model = ns.model('Login', {
        'email': fields.String(required=True),
        'password': fields.String(required=True)
    })

    @ns.expect(login_model)
    def post(self):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Mock user validation (replace with real user DB check)
        if email == 'test@example.com' and password == 'password':
            access_token = create_access_token(
                identity=email,
                expires_delta=timedelta(hours=24)
            )
            return {'token': access_token}, 200
        return {'message': 'Invalid credentials'}, 401


# Payment initialization endpoint
@ns.route('/payment/initiate')
class PaymentInitiate(Resource):
    payment_model = ns.model('Payment', {
        'amount': fields.Float(required=True),
        'currency': fields.String(required=True, default='NGN'),
        'customer_email': fields.String(required=True),
        'customer_name': fields.String(required=True),
        'invoice_id': fields.Integer(required=True)
    })

    @ns.expect(payment_model)
    @require_jwt
    def post(self):
        data = request.get_json()
        amount = data.get('amount')
        currency = data.get('currency')
        customer_email = data.get('customer_email')
        customer_name = data.get('customer_name')
        invoice_id = data.get('invoice_id')
        tx_ref = f"TX-{datetime.now(timezone).strftime('%Y%m%d%H%M%S')}"

        # Get user from JWT
        user_email = request.user['email']
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return {'message': 'User not found'}, 404

        # Create pending payment record
        payment = Payment(
            invoice_id=invoice_id,
            client_id=user.id,
            transaction_id=tx_ref,
            amount=amount,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()

        # Flutterwave payment initialization
        headers = {
            'Authorization': f'Bearer {FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'tx_ref': tx_ref,
            'amount': amount,
            'currency': currency,
            'redirect_url': 'https://your-app.com/payment/callback',  # Update with your redirect URL
            'customer': {
                'email': customer_email,
                'name': customer_name
            },
            'customizations': {
                'title': 'Your App Payment',
                'description': 'Payment for services'
            }
        }

        response = requests.post(
            'https://api.flutterwave.com/v3/payments',
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            payment_data = response.json()
            return {
                'payment_url': payment_data['data']['link'],
                'tx_ref': tx_ref,
                'payment_id': payment.id
            }, 200
        return {'message': 'Failed to initiate payment'}, 400

# Payment verification endpoint (for webhook or redirect callback)
@ns.route('/payment/verify/<string:tx_ref>')
class PaymentVerify(Resource):
    @require_jwt
    def get(self, tx_ref):
        headers = {
            'Authorization': f'Bearer {FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f'https://api.flutterwave.com/v3/transactions/{tx_ref}/verify',
            headers=headers
        )

        if response.status_code == 200:
            verification_data = response.json()
            if verification_data['data']['status'] == 'successful':
                # Update payment status in database
                payment = Payment.query.filter_by(transaction_id=tx_ref).first()
                if payment:
                    payment.status = 'completed'
                    payment.paid_at = datetime.now(timezone.utc)
                    db.session.commit()
                return {'message': 'Payment verified successfully', 'data': verification_data['data']}, 200
            return {'message': 'Payment not successful'}, 400
        return {'message': 'Failed to verify payment'}, 400

# Webhook endpoint for Flutterwave notifications
@ns.route('/payment/webhook')
class PaymentWebhook(Resource):
    def post(self):
        data = request.get_json()
        tx_ref = data.get('txRef')
        status = data.get('status')

        if status == 'successful':
            # Verify payment with Flutterwave API
            headers = {
                'Authorization': f'Bearer {FLUTTERWAVE_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.get(
                f'https://api.flutterwave.com/v3/transactions/{tx_ref}/verify',
                headers=headers
            )
            if response.status_code == 200 and response.json()['data']['status'] == 'successful':
                # Update payment status in database
                payment = Payment.query.filter_by(transaction_id=tx_ref).first()
                if payment:
                    payment.status = 'completed'
                    payment.paid_at = datetime.now(timezone.utc)
                    db.session.commit()
                return {'message': 'Webhook processed successfully'}, 200
        return {'message': 'Webhook processing failed'}, 400

# Payment list endpoint
@ns.route('/payments')
class PaymentList(Resource):
    @require_jwt
    def get(self):
        user_email = request.user['email']
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return {'message': 'User not found'}, 404

        payments = Payment.query.filter_by(client_id=user.id).all()
        return {'payments': [payment.to_dict() for payment in payments]}, 200

# Payment detail endpoint
@ns.route('/payments/<int:payment_id>')
class PaymentDetail(Resource):
    @require_jwt
    def get(self, payment_id):
        user_email = request.user['email']
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return {'message': 'User not found'}, 404

        payment = Payment.query.filter_by(id=payment_id, client_id=user.id).first()
        if not payment:
            return {'message': 'Payment not found'}, 404

        return {'payment': payment.to_dict()}, 200

# Function to register the namespace with the main API
def register_payments(api):
    api.add_namespace(ns)
=======
from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Payment, Invoice
from http import HTTPStatus
from middlewares.auth_middleware import role_required
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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
        @role_required('freelancer')
        def get(self):
            """List all payments for the authenticated freelancer with pagination"""
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
        @role_required('freelancer')
        def get(self, id):
            """Get a specific payment"""
            freelancer_id = get_jwt_identity()
            invoices = Invoice.query.filter_by(freelancer_id=freelancer_id).all()
            invoice_ids = [invoice.id for invoice in invoices]
            payment = Payment.query.filter(Payment.id == id, Payment.invoice_id.in_(invoice_ids)).first()
            if not payment:
                logger.error(f"Payment {id} not found for freelancer {freelancer_id}")
                return {'message': 'Payment not found'}, HTTPStatus.NOT_FOUND
            return payment, HTTPStatus.OK
>>>>>>> 6284299c2bcbda853f91d0ebe69a81de27ea1b32
