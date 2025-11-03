from src.extensions import db
from sqlalchemy.dialects.postgresql import NUMERIC
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'), nullable=True)
    transaction_id = db.Column(db.String(100))
    amount = db.Column(NUMERIC(10, 2))
    paid_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(50))
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String, nullable=True)

    # relationships are defined on the profile models to avoid duplicate backref errors
    # access payments from profiles via ClientProfile.payments and FreelancerProfile.payments

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'client_id': self.client_id,
            'freelancer_id': self.freelancer_id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method
        }

class PaymentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True
