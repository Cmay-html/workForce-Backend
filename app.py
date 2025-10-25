from flask import Flask
from flask_restx import Api
from extensions import db, jwt
from flask_cors import CORS
from flask_migrate import Migrate
from models import Deliverable, Invoice, Message, Milestone, Payment, ProjectApplication, Project, Review, Skill, TimeLog, User, FreelancerProfile, ClientProfile
from routes.payments import register_payments
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db
from routes.auth import auth_ns
from routes.freelance import freelance_ns
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configure from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    Migrate(app, db)
    JWTManager(app)
    Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

    # Initialize API
    api = Api(app, prefix='/api', doc='/docs', title='Freelance Platform API')
    api.add_namespace(auth_ns)
    api.add_namespace(freelance_ns)

    # Register routes
    register_payments(api)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)