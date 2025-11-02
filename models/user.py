from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Optional for OAuth users
    role = db.Column(db.String(20), nullable=False)
    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Google OAuth ID
    is_verified = db.Column(db.Boolean, default=True)  # OAuth users are pre-verified
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)

    # One-to-one relationships to profiles
    client_profile = db.relationship(
        'ClientProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')
    freelancer_profile = db.relationship(
        'FreelancerProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_verified': self.is_verified,
            'google_id': self.google_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

    @classmethod
    def get_or_create_from_google(cls, google_user_info, role='freelancer'):
        """Get or create user from Google OAuth info"""
        google_id = google_user_info.get('sub')
        email = google_user_info.get('email')

        # Try to find existing user by Google ID or email
        user = cls.query.filter(
            (cls.google_id == google_id) | (cls.email == email)
        ).first()

        if user:
            # Update Google ID if not set
            if not user.google_id and google_id:
                user.google_id = google_id
                db.session.commit()
            return user

        # Create new user
        user = cls(
            email=email,
            google_id=google_id,
            role=role,
            is_verified=True,  # Google OAuth users are pre-verified
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(user)
        db.session.commit()

        # Create profile based on role
        if role == 'freelancer':
            from models import FreelancerProfile
            freelancer_profile = FreelancerProfile(
                user_id=user.id,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(freelancer_profile)
            db.session.commit()

        return user


class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    profile_picture_uri = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='client_profile')

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
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='freelancer_profile')

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
