from flask import Flask
from flask_restx import Api
from extensions import db, migrate, jwt, api
from flask_cors import CORS
from flask_migrate import Migrate
from models import Deliverable, Invoice, Message, Milestone, Payment, ProjectApplication, Project, Review, Skill, TimeLog, User, FreelancerProfile, ClientProfile, Dispute, Policy
from config import DevConfig  
from routes import init_routes

def create_app(config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    CORS(app)
    migrate.init_app(app, db)  
    api.init_app(app)          
    init_routes()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)