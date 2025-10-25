`import os
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from functools import wraps
from flask import request
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from models.payment import Payment
from models.user import ClientProfile
from models.invoice import Invoice
from extensions import db

# Load environment variables
load_dotenv()

# Create namespace for payments
ns = Namespace('payments', description='Payment Operations')

# Role-based JWT Authentication Decorator
def require_role(role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated(*args, **kwargs):
            user_email = get_jwt_identity()
            user = ClientProfile.query.filter_by(email=user_email).first()
            if not user or user.role != role:
                return {'message': f'Only {role}s are authorized'}, 403
            request.user = user
            return f(*args, **kwargs)
        return decorated
    return decorator

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

        # Validate client credentials (assumes ClientProfile has check_password)
        client = ClientProfile.query.filter_by(email=email).first()
        if client and client.check_password(password):  # Replace with real password check
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
    @require_role('client')
    def post(self):
        data = request.get_json()
        amount = data.get('amount')
        currency = data.get('currency')
        customer_email = data.get('customer_email')
        customer_name = data.get('customer_name')
        invoice_id = data.get('invoice_id')

        # Validate inputs
        if amount <= 0:
            return {'message': 'Amount must be positive'}, 400
        if currency not in ['NGN', 'USD']:  # Add supported currencies
            return {'message': 'Unsupported currency'}, 400

        # Get client from JWT
        client = request.user
        invoice = Invoice.query.get_or_404(invoice_id)
        if invoice.client_id != client.id:
            return {'message': 'Unauthorized invoice'}, 403

        # Generate unique transaction reference
        tx_ref = f"TX-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{client.id}"

        try:
            # Create pending payment record
            payment = Payment(
                invoice_id=invoice_id,
                client_id=client.id,
                # freelancer_id=invoice.freelancer_id,  # Uncomment if Payment model has freelancer_id
                transaction_id=tx_ref,
                amount=amount,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': f'Failed to create payment: {str(e)}'}, 500

        # Mock payment processing (replace with actual payment gateway logic)
        try:
            # Simulate payment initiation (e.g., redirect to a payment page)
            payment_url = f"https://your-app.com/mock-payment?tx_ref={tx_ref}"
            return {
                'payment_url': payment_url,
                'tx_ref': tx_ref,
                'payment_id': payment.id
            }, 200
        except Exception as e:
            return {'message': f'Failed to initiate payment: {str(e)}'}, 400

# Payment verification endpoint
@ns.route('/payment/verify/<string:tx_ref>')
class PaymentVerify(Resource):
    @require_role('client')
    def get(self, tx_ref):
        client = request.user
        payment = Payment.query.filter_by(transaction_id=tx_ref, client_id=client.id).first()
        if not payment:
            return {'message': 'Payment not found or unauthorized'}, 404

        # Mock verification (replace with actual payment gateway verification)
        try:
            # Simulate checking payment status (e.g., via database or external API)
            if payment.status == 'pending':  # Simulate successful payment for demo
                payment.status = 'completed'
                payment.paid_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'message': 'Payment verified successfully',
                    'data': {
                        'transaction_id': tx_ref,
                        'status': payment.status,
                        'amount': float(payment.amount),
                        'paid_at': payment.paid_at.isoformat()
                    }
                }, 200
            return {'message': 'Payment not successful'}, 400
        except Exception as e:
            return {'message': f'Failed to verify payment: {str(e)}'}, 400

# Webhook endpoint for payment notifications
@ns.route('/payment/webhook')
class PaymentWebhook(Resource):
    def post(self):
        data = request.get_json()
        tx_ref = data.get('txRef')
        status = data.get('status')

        if status != 'successful':
            return {'message': 'Webhook processing skipped: Payment not successful'}, 200

        try:
            payment = Payment.query.filter_by(transaction_id=tx_ref).first()
            if payment:
                payment.status = 'completed'
                payment.paid_at = datetime.now(timezone.utc)
                db.session.commit()
                # Notify freelancer (assumes Invoice has freelancer_id)
                invoice = Invoice.query.get(payment.invoice_id)
                if invoice and invoice.freelancer_id:
                    notify_freelancer(invoice.freelancer_id, payment)
                return {'message': 'Webhook processed successfully'}, 200
            return {'message': 'Payment not found'}, 404
        except Exception as e:
            db.session.rollback()
            return {'message': f'Webhook processing failed: {str(e)}'}, 400

# Payment list endpoint
@ns.route('/payments')
class PaymentList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, default=1)
    parser.add_argument('per_page', type=int, default=10)

    @ns.expect(parser)
    @require_role('client')
    def get(self):
        args = self.parser.parse_args()
        client = request.user
        payments = Payment.query.filter_by(client_id=client.id).paginate(
            page=args['page'], per_page=args['per_page']
        )
        return {
            'payments': [payment.to_dict() for payment in payments.items],
            'total': payments.total,
            'pages': payments.pages
        }, 200

# Payment detail endpoint
@ns.route('/payments/<int:payment_id>')
class PaymentDetail(Resource):
    @require_role('client')
    def get(self, payment_id):
        client = request.user
        payment = Payment.query.filter_by(id=payment_id, client_id=client.id).first()
        if not payment:
            return {'message': 'Payment not found or unauthorized'}, 404
        return {'payment': payment.to_dict()}, 200

# Placeholder for freelancer notification
def notify_freelancer(freelancer_id, payment):
    # Implement notification logic (e.g., email, in-app)
    pass

# Function to register the namespace with the main API
def register_payments(api):
    api.add_namespace(ns)