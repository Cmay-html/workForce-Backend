from ..extensions import db
from sqlalchemy.dialects.postgresql import NUMERIC
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'))
    amount = db.Column(NUMERIC(10, 2))
    generated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(50))

    # payments = db.relationship("Payment", backref="invoices")

    def to_dict(self):
        return {
            'id': self.id,
            'milestone_id': self.milestone_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'status': self.status
        }

class InvoiceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Invoice
        load_instance = True