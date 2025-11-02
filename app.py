# app.py
from flask import Flask, request
from flask_restx import Api
from extensions import db, migrate, jwt, api, ma
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from models import (
    Deliverable, Invoice, Message, Milestone, Payment, 
    ProjectApplication, Project, Review, Skill, TimeLog, 
    User, FreelancerProfile, ClientProfile, Dispute, Policy
)
from config import DevConfig
from routes import init_routes
from flask_mail import Mail

mail = Mail()

def create_app(config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    # Configure from environment variables if not in config
    if 'JWT_ACCESS_TOKEN_EXPIRES' not in app.config:
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
    if 'JWT_REFRESH_TOKEN_EXPIRES' not in app.config:
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  
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
