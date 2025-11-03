# app.py
import os
import logging
from flask import Flask, request
from flask_restx import Api
from src.extensions import db, migrate, jwt, api, ma, mail
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from src.models import (
    Deliverable, Invoice, Message, Milestone, Payment,
    ProjectApplication, Project, Review, Skill, TimeLog,
    User, FreelancerProfile, ClientProfile, Dispute, Policy
)
from src.config import DevConfig
from src.routes import init_routes
from src.routes.routes import auth_ns
from src.routes.applications import register_routes as register_applications
from src.routes.invoices import register_routes as register_invoices
from src.routes.receipts import register_routes as register_receipts
from src.routes.payments import register_routes as register_payments
from src.routes.freelancer import register_routes as register_freelancer

def create_app(config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    # Ensure database URI is set
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb')

    # Configure from environment variables if not in config
    if 'JWT_ACCESS_TOKEN_EXPIRES' not in app.config:
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
    if 'JWT_REFRESH_TOKEN_EXPIRES' not in app.config:
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://6908506926707cce75213659--workforceflows.netlify.app",
                "https://workforceflows.netlify.app",
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
            "supports_credentials": True
        }
    })
    migrate.init_app(app, db)
    api.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    init_routes()

    @app.before_request
    def log_request_info():
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        app.logger.error('Exception: %s', str(e))
        app.logger.error('Traceback: %s', traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}, 500

    return app

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'bd6f47d5fbe6130531225d993ce47f56')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_flask_secret_key')

# Initialize extensions
jwt = JWTManager(app)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://6908506926707cce75213659--workforceflows.netlify.app",
            "https://workforceflows.netlify.app",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        "supports_credentials": True
    }
})
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
