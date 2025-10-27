from extensions import db
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    budget = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, onupdate=datetime.now(timezone.utc))

    # Relationships
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('ProjectApplication', backref='project', lazy=True, cascade='all, delete-orphan')
    time_logs = db.relationship('TimeLog', backref='project', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='project', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'budget': float(self.budget) if self.budget is not None else None,
            'status': self.status,
            'client_id': self.client_id,
            'freelancer_id': self.freelancer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class ProjectSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        load_instance = True
        include_relationships = True  # Include related objects (e.g., milestones)