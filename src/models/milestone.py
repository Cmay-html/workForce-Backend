from src.extensions import db
from sqlalchemy.dialects.postgresql import NUMERIC
from datetime import date, datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    amount = db.Column(NUMERIC(10, 2))
    status = db.Column(db.String(20))
    
    # Define relationship with project
    project = db.relationship('Project', backref=db.backref('milestones', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'status': self.status
        }

class MilestoneSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Milestone
        load_instance = True