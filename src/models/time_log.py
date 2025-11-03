from src.extensions import db
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class TimeLog(db.Model):
    __tablename__ = 'time_logs'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'freelancer_id': self.freelancer_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

class TimeLogSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TimeLog
        load_instance = True