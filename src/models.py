from extensions import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    role = db.Column(db.String, default='user')

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'), nullable=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String, nullable=True)
    status = db.Column(db.String, default='pending')
    payment_date = db.Column(db.Date, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String, nullable=True)

class FreelancerProfile(db.Model):
    __tablename__ = 'freelancer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=True)
    role = db.Column(db.String, default='freelancer')

class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    role = db.Column(db.String, default='client')

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'), nullable=False)
    status = db.Column(db.String, default='pending')

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String, default='open')