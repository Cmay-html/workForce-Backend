from extensions import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime

class Policy(db.Model):
    __tablename__ = 'policies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    content = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PolicySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Policy
        load_instance = True