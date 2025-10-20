from ..extensions import db
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='freelancer')  # 'client', 'freelancer', 'admin'
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)  # JSON string or comma-separated
    rating = db.Column(db.Float, default=0.0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships will be added when other models are implemented
    # projects_as_client = db.relationship('Project', backref='client', lazy=True, foreign_keys='Project.client_id')
    # projects_as_freelancer = db.relationship('Project', backref='freelancer', lazy=True, foreign_keys='Project.freelancer_id')
    # invoices = db.relationship('Invoice', backref='user', lazy=True)
    # payments = db.relationship('Payment', backref='user', lazy=True)
    # chats = db.relationship('Chat', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        return create_access_token(identity=self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'skills': self.skills,
            'rating': self.rating,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100))
    company_size = db.Column(db.String(20))  # 'startup', 'small', 'medium', 'large', 'enterprise'
    industry = db.Column(db.String(50))
    website = db.Column(db.String(255))
    location = db.Column(db.String(100))
    budget_range = db.Column(db.String(20))  # 'low', 'medium', 'high', 'enterprise'
    preferred_payment_terms = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = db.relationship('User', backref=db.backref('client_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'company_size': self.company_size,
            'industry': self.industry,
            'website': self.website,
            'location': self.location,
            'budget_range': self.budget_range,
            'preferred_payment_terms': self.preferred_payment_terms,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Freelancer(db.Model):
    __tablename__ = 'freelancers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hourly_rate = db.Column(db.Float)
    availability_status = db.Column(db.String(20), default='available')  # 'available', 'busy', 'unavailable'
    experience_years = db.Column(db.Integer)
    portfolio_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    languages = db.Column(db.Text)  # JSON string of spoken languages
    timezone = db.Column(db.String(50))
    completed_projects = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    response_time_hours = db.Column(db.Float)  # Average response time in hours
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = db.relationship('User', backref=db.backref('freelancer_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hourly_rate': self.hourly_rate,
            'availability_status': self.availability_status,
            'experience_years': self.experience_years,
            'portfolio_url': self.portfolio_url,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'languages': self.languages,
            'timezone': self.timezone,
            'completed_projects': self.completed_projects,
            'total_earnings': self.total_earnings,
            'response_time_hours': self.response_time_hours,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(50))
    permissions = db.Column(db.Text)  # JSON string of permissions
    last_login = db.Column(db.DateTime)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = db.relationship('User', backref=db.backref('admin_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'department': self.department,
            'permissions': self.permissions,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }