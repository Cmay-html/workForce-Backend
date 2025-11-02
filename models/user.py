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

    # One-to-one relationships to profiles
    client_profile = db.relationship(
        'ClientProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')
    freelancer_profile = db.relationship(
        'FreelancerProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        return create_access_token(identity=self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

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

    user = db.relationship('User', back_populates='client_profile')

    # payments = db.relationship("Payment", backref="client")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'industry': self.industry,
            'bio': self.bio,
            'website': self.website,
            'profile_picture_uri': self.profile_picture_uri,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

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

    user = db.relationship('User', back_populates='freelancer_profile')
    # many-to-many with skills will be defined in skill models
    # payments = db.relationship("Payment", backref="freelancer")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate is not None else None,
            'bio': self.bio,
            'experience': self.experience,
            'portfolio_links': self.portfolio_links,
            'profile_picture_uri': self.profile_picture_uri,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_relationships = True
        include_fk = True

class ClientProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ClientProfile
        load_instance = True
        include_relationships = False
        include_fk = True

class FreelancerProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FreelancerProfile
        load_instance = True
        include_relationships = False
        include_fk = True
