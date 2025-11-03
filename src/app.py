"""Flask application factory and setup."""
import os
import logging
from flask import Flask, request
from flask_cors import CORS
from .extensions import db, migrate, jwt, api, ma, mail
from .config import DevConfig
from .routes import init_routes
from .routes.auth import auth_ns
from .routes.applications import register_routes as register_applications
from .routes.invoices import register_routes as register_invoices
from .routes.receipts import register_routes as register_receipts
from .routes.payments import register_routes as register_payments
from .routes.freelancer import register_routes as register_freelancer
from . import models  # ensure models are imported for mapper configuration


def create_app(config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    # Ensure database URI is set (dev fallback only). In production, require DATABASE_URL.
    if not app.config.get('SQLALCHEMY_DATABASE_URI') and config is DevConfig:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb'
        )

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://6908506926707cce75213659--workforceflows.netlify.app",
                "https://workforceflows.netlify.app",
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
            "supports_credentials": True,
            "expose_headers": ["X-Total-Count", "X-Page-Count"],
        }
    })
    migrate.init_app(app, db)
    api.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    mail.init_app(app)

    # Optional safety net: create tables automatically if allowed (useful on fresh DBs)
    if os.getenv('AUTO_CREATE_TABLES', 'true').lower() == 'true':
        try:
            with app.app_context():
                db.create_all()
        except Exception as e:
            app.logger.error(f"Auto table creation failed: {e}")

    # Register namespaces
    init_routes()
    api.add_namespace(auth_ns, path='/api/auth')
    register_applications(api.namespace('applications', description='Application Management', path='/api/applications'))
    register_invoices(api.namespace('invoices', description='Invoice Management', path='/api/invoices'))
    register_receipts(api.namespace('freelancer/payments', description='Freelancer Payment History', path='/api/freelancer/payments'))
    register_payments(api.namespace('client/payments', description='Client Payment Operations', path='/api/client/payments'))
    register_freelancer(api.namespace('freelancer', description='Freelancer Journey', path='/api/freelancer'))

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

    # Logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    return app


if __name__ == '__main__':
    # Local debug runner
    app = create_app()
    app.run(debug=True)
