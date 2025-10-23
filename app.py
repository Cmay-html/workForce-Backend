from flask import Flask
from flask_restx import Api
from extensions import db
from flask_cors import CORS
from flask_migrate import Migrate
from models import Deliverable, Invoice, Message, Milestone, Payment, ProjectApplication, Project, Review, Skill, TimeLog, User, FreelancerProfile, ClientProfile
from flask_jwt_extended import JWTManager
from routes.auth import auth_ns


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    CORS(app)

    migrate = Migrate(app, db)

    api = Api(app, doc="/docs")

    return app


app = Flask(__name__)

# Configure CORS
CORS(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
jwt = JWTManager(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'your-database-uri'  # e.g., sqlite:///app.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Flask-RESTX API
api = Api(app, prefix='/api', doc='/docs')
api.add_namespace(auth_ns)

# Initialize Flask-Limiter
limiter.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)