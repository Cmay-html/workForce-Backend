# routes/payments.py
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.extensions import db
from src.models.user import ClientProfile, FreelancerProfile, User
from src.models.invoice import Invoice
from src.models.payment import Payment
from http import HTTPStatus
import logging
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

logger = logging.getLogger(__name__)
ns = Namespace('client/payments', description='Client Payment Operations')

FLUTTERWAVE_SECRET_KEY = os.getenv('FLUTTERWAVE_SECRET_KEY')
FLUTTERWAVE_API_URL = 'https://api.flutterwave.com/v3/payments'

def require_role(role):
    def decorator(f):
        @jwt_required()
        def wrapped(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != role:
                logger.error(f"Unauthorized access by {get_jwt_identity()} with role {claims.get('role')}")
                return {'message': f'Only {role}s allowed'}, HTTPStatus.FORBIDDEN
            user_email = get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
            if not user or not user.client_profile:
                logger.error(f"Client profile not found for {user_email}")
                return {'message': 'Profile not found'}, HTTPStatus.NOT_FOUND
            request.user = user.client_profile
            return f(*args, **kwargs)
        return wrapped
    return decorator

payment_model = ns.model('Payment', {
    'id': fields.Integer,
    'invoice_id': fields.Integer,
    'amount': fields.Float,
    'status': fields.String,
    'payment_date': fields.Date,
    'transaction_id': fields.String
})

initiate_parser = reqparse.RequestParser()
initiate_parser.add_argument('amount', type=float, required=True)
initiate_parser.add_argument('currency', type=str, required=True)
initiate_parser.add_argument('customer_email', type=str, required=True)
initiate_parser.add_argument('customer_name', type=str, required=True)
initiate_parser.add_argument('invoice_id', type=int, required=True)

@ns.route('')
class ClientPayments(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, default=1)
    parser.add_argument('per_page', type=int, default=10)

    @ns.expect(parser)
    @require_role('client')
    @ns.marshal_list_with(payment_model)
    def get(self):
        args = self.parser.parse_args()
        client = request.user
        payments = Payment.query.filter_by(client_id=client.id).paginate(
            page=args['page'], per_page=args['per_page'], error_out=False
        )
        logger.info(f"Client {client.id} retrieved payments")
        return [{
            'id': p.id,
            'invoice_id': p.invoice_id,
            'amount': p.amount,
            'status': p.status,
            'payment_date': p.payment_date,
            'transaction_id': p.transaction_id
        } for p in payments.items], HTTPStatus.OK

@ns.route('/initiate')
class InitiatePayment(Resource):
    @ns.expect(initiate_parser)
    @require_role('client')
    def post(self):
        args = initiate_parser.parse_args()
        client = request.user
        invoice = Invoice.query.get_or_404(args['invoice_id'])
        if invoice.client_id != client.id:
            logger.error(f"Client {client.id} attempted to pay unauthorized invoice {args['invoice_id']}")
            return {'message': 'Unauthorized invoice'}, HTTPStatus.FORBIDDEN

        headers = {
            'Authorization': f'Bearer {FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'tx_ref': f'kazi_flow_{invoice.id}_{int(datetime.now().timestamp())}',
            'amount': args['amount'],
            'currency': args['currency'],
            'redirect_url': 'http://localhost:5000/client/payments/verify',
            'customer': {
                'email': args['customer_email'],
                'name': args['customer_name']
            }
        }
        try:
            response = requests.post(FLUTTERWAVE_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data['status'] != 'success':
                logger.error(f"Flutterwave payment initiation failed: {data}")
                return {'message': 'Payment initiation failed'}, HTTPStatus.BAD_REQUEST
        except requests.RequestException as e:
            logger.error(f"Flutterwave request failed: {e}")
            return {'message': 'Payment gateway error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        payment = Payment(
            invoice_id=args['invoice_id'],
            client_id=client.id,
            freelancer_id=invoice.freelancer_id,
            amount=args['amount'],
            transaction_id=payload['tx_ref'],
            status='pending',
            payment_date=datetime.now(timezone.utc).date()
        )
        db.session.add(payment)
        db.session.commit()
        logger.info(f"Payment initiated by client {client.id} for invoice {args['invoice_id']}")
        return {
            'message': 'Payment initiated',
            'payment_id': payment.id,
            'payment_url': data['data']['link']
        }, HTTPStatus.OK

@ns.route('/verify/<string:tx_ref>')
class VerifyPayment(Resource):
    def get(self, tx_ref):
        headers = {
            'Authorization': f'Bearer {FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(f'https://api.flutterwave.com/v3/transactions/{tx_ref}/verify', headers=headers)
            response.raise_for_status()
            data = response.json()
            if data['status'] != 'success':
                logger.error(f"Flutterwave verification failed: {data}")
                return {'message': 'Payment verification failed'}, HTTPStatus.BAD_REQUEST
            payment = Payment.query.filter_by(transaction_id=tx_ref).first()
            if not payment:
                logger.error(f"Payment not found for tx_ref {tx_ref}")
                return {'message': 'Payment not found'}, HTTPStatus.NOT_FOUND
            payment.status = data['data']['status']
            payment.paid_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Payment {payment.id} verified for tx_ref {tx_ref}")
            return {'message': 'Payment verified', 'status': payment.status}, HTTPStatus.OK
        except requests.RequestException as e:
            logger.error(f"Flutterwave verification failed: {e}")
            return {'message': 'Verification error'}, HTTPStatus.INTERNAL_SERVER_ERROR

def register_routes(ns):
    pass