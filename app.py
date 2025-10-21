from flask import Flask
from flask_restx import Api
from extensions import db
from flask_cors import CORS
from flask_migrate import Migrate
from models import Deliverable, Invoice, Message, Milestone, Payment, ProjectApplication, Project, Review, Skill, TimeLog, User, FreelancerProfile, ClientProfile


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    CORS(app)

    migrate = Migrate(app, db)

    api = Api(app, doc="/docs")

    return app
