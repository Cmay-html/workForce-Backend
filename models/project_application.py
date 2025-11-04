from extensions import db
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class ProjectApplication(db.Model):
    __tablename__ = 'project_applications'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'))
    status = db.Column(db.String(50))
    applied_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'freelancer_id': self.freelancer_id,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }

class ProjectApplicationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProjectApplication
        load_instance = True