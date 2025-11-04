from flask import Flask
from .extensions import db, ma
from models.user import User, ClientProfile, FreelancerProfile

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db.init_app(app)
ma.init_app(app)

with app.app_context():
    # Create tables
    db.create_all()
    
    # Create test user
    user = User(email='test@example.com', role='client')
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    
    # Create client profile
    profile = ClientProfile(user_id=user.id, company_name='Test Co')
    db.session.add(profile)
    db.session.commit()
    
    # Query and print
    print("User:", User.query.first().to_dict())
    print("Profile:", ClientProfile.query.first().to_dict() if hasattr(ClientProfile, 'to_dict') else ClientProfile.query.first())