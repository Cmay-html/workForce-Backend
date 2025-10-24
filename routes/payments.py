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