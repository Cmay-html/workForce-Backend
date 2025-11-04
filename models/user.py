# models/user.py
from extensions import db, ma
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        return create_access_token(identity=self.id)

class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    profile_picture_uri = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class FreelancerProfile(db.Model):
    __tablename__ = 'freelancer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hourly_rate = db.Column(db.Numeric(10, 2))
    bio = db.Column(db.Text)
    experience = db.Column(db.Text)
    portfolio_links = db.Column(db.Text)
    profile_picture_uri = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    skills = db.relationship('Skill', secondary='freelancer_skills', backref='freelancers')

# Corrected Schemas
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        fields = ("id", "email", "role")

class ClientProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ClientProfile
        load_instance = True

class FreelancerProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FreelancerProfile
        load_instance = True