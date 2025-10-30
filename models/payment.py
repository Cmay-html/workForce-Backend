from extensions import db
from sqlalchemy.dialects.postgresql import NUMERIC
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'))
    transaction_id = db.Column(db.String(100))
    amount = db.Column(NUMERIC(10, 2))
    paid_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'client_id': self.client_id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'status': self.status
        }

class PaymentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True