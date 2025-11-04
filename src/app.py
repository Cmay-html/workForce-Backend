"""Flask application factory and setup."""
import os
import logging
from flask import Flask, request
from flask_cors import CORS
from .extensions import db, migrate, jwt, api, ma, mail, socketio
from .config import DevConfig
from .routes import init_routes
from .routes.auth import auth_ns
from .routes.applications import register_routes as register_applications
from .routes.invoices import register_routes as register_invoices
from .routes.receipts import register_routes as register_receipts
from .routes.payments import register_routes as register_payments
from .routes.freelancer import register_routes as register_freelancer
from .routes.freelancers_list import api as freelancers_ns
from .routes.chat import api as chat_ns
from .routes.projects import api as projects_ns
from . import models  # ensure models are imported for mapper configuration


def create_app(config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config)
    # Allow both with and without trailing slashes for all routes (helps with preflights)
    app.url_map.strict_slashes = False

    # Ensure database URI is set (dev fallback only). In production, require DATABASE_URL.
    if not app.config.get('SQLALCHEMY_DATABASE_URI') and config is DevConfig:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/workdb'
        )

    # Initialize extensions
    db.init_app(app)
    # Allow CORS for all API routes and non-API aliases (e.g., /client/*)
    allowed_origins = [
        os.getenv("FRONTEND_ORIGIN", ""),
        "https://6908506926707cce75213659--workforceflows.netlify.app",
        "https://workforceflows.netlify.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    # Remove empty strings to avoid invalid headers
    allowed_origins = [o for o in allowed_origins if o]

    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
            "supports_credentials": True,
            "expose_headers": ["X-Total-Count", "X-Page-Count"],
        }
    })
    migrate.init_app(app, db)
    api.init_app(app)
    jwt.init_app(app)
    # Initialize Socket.IO with same allowed origins as CORS
    try:
        origins = [o for o in allowed_origins if o]
    except Exception:
        origins = ['*']
    socketio.init_app(app, cors_allowed_origins=origins)

    # JWT error handlers for clearer client feedback
    @jwt.unauthorized_loader
    def _jwt_unauthorized_callback(err_msg):
        return {"success": False, "message": f"Unauthorized: {err_msg}"}, 401

    @jwt.invalid_token_loader
    def _jwt_invalid_token_callback(err_msg):
        # Common when old tokens have integer sub (subject) and library expects string
        return {"success": False, "message": f"Invalid token: {err_msg}. Please log in again."}, 401

    @jwt.expired_token_loader
    def _jwt_expired_token_callback(jwt_header, jwt_payload):
        return {"success": False, "message": "Token has expired. Please log in again."}, 401

    @jwt.needs_fresh_token_loader
    def _jwt_needs_fresh_callback(jwt_header, jwt_payload):
        return {"success": False, "message": "Fresh token required."}, 401

    @jwt.revoked_token_loader
    def _jwt_revoked_token_callback(jwt_header, jwt_payload):
        return {"success": False, "message": "Token has been revoked."}, 401
    ma.init_app(app)
    mail.init_app(app)

    # Optional safety net: create tables automatically if allowed (useful on fresh DBs)
    if os.getenv('AUTO_CREATE_TABLES', 'true').lower() == 'true':
        try:
            with app.app_context():
                db.create_all()
        except Exception as e:
            app.logger.error(f"Auto table creation failed: {e}")

    # Optional safety net: ensure critical columns exist (helps when migrations are skipped)
    if os.getenv('AUTO_PATCH_SCHEMA', 'true').lower() == 'true':
        try:
            from sqlalchemy import text
            with app.app_context():
                # Add users.verification_token if missing
                db.session.execute(text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='users' AND column_name='verification_token'
                        ) THEN
                            ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
                        END IF;
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='users' AND column_name='token_expires_at'
                        ) THEN
                            ALTER TABLE users ADD COLUMN token_expires_at TIMESTAMP;
                        END IF;
                    END $$;
                    """
                ))
                db.session.commit()
        except Exception as e:
            app.logger.error(f"Schema auto-patch failed: {e}")

    # Register namespaces
    init_routes()
    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(projects_ns, path='/api/projects')
    api.add_namespace(freelancers_ns, path='/api/freelancers')
    api.add_namespace(chat_ns, path='/api/chat')
    register_applications(api.namespace('applications', description='Application Management', path='/api/applications'))
    register_invoices(api.namespace('invoices', description='Invoice Management', path='/api/invoices'))
    register_receipts(api.namespace('freelancer/payments', description='Freelancer Payment History', path='/api/freelancer/payments'))
    register_payments(api.namespace('client/payments', description='Client Payment Operations', path='/api/client/payments'))
    register_freelancer(api.namespace('freelancer', description='Freelancer Journey', path='/api/freelancer'))

    @app.before_request
    def log_request_info():
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())

    # Legacy alias: forward /client/projects to /api/projects
    @app.route('/client/projects', methods=['GET', 'POST', 'OPTIONS'])
    def _client_projects_alias():
        from flask import redirect, url_for
        if request.method == 'OPTIONS':
            # Preflight - return 204 with CORS headers
            return '', 204
        # Forward GET/POST to the actual projects endpoint
        # Since Flask-RESTX handles /api/projects, we need to proxy the request
        from .routes.projects import api as projects_ns
        # Get the actual resource class for the list endpoint
        from .routes.projects import ProjectList
        resource = ProjectList()
        if request.method == 'GET':
            return resource.get()
        elif request.method == 'POST':
            return resource.post()

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        app.logger.error('Exception: %s', str(e))
        app.logger.error('Traceback: %s', traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}, 500

    # Logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Simple DB health endpoint to inspect users table columns
    @app.get('/_dbcheck')
    def _dbcheck():
        from sqlalchemy import text
        rows = db.session.execute(text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users'
            ORDER BY column_name
            """
        )).mappings().all()
        cols = [r['column_name'] for r in rows]
        return {"users_columns": cols}, 200

    return app


if __name__ == '__main__':
    # Local debug runner
    app = create_app()
    app.run(debug=True)
