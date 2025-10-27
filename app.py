# app.py
from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Your routes
from routes.freelancer import register_routes as register_freelancer
from routes.payments import register_routes as register_payments

# Other team routes
from routes.applications import register_routes as register_applications
from routes.auth import auth_ns
from routes.invoices import register_routes as register_invoices
from routes.receipts import register_routes as register_receipts

# Core extensions
from extensions import db, migrate

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'bd6f47d5fbe6130531225d993ce47f56')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_flask_secret_key')

# Initialize extensions
jwt = JWTManager(app)
CORS(app)
db.init_app(app)
migrate.init_app(app, db)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize API
api = Api(
    app,
    title='Kazi Flow API',
    description='Freelancer and Client APIs',
    security='Bearer'
)

# Register namespaces
register_applications(api.namespace('applications', description='Application Management'))
api.add_namespace(auth_ns, path='/auth')
register_invoices(api.namespace('invoices', description='Invoice Management'))
register_receipts(api.namespace('freelancer/payments', description='Freelancer Payment History'))
register_payments(api.namespace('client/payments', description='Client Payment Operations'))
register_freelancer(api.namespace('freelancer', description='Freelancer Journey'))

if __name__ == '__main__':
    app.run(debug=True)