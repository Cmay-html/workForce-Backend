from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_marshmallow import Marshmallow  

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()  
api = Api(title='FreelanceFlow API', version='1.0', description='API for freelance management', doc='/api/docs')