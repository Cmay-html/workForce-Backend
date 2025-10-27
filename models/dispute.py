from extensions import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime

class Dispute(db.Model):
    __tablename__ = 'disputes'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class DisputeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Dispute
        load_instance = True