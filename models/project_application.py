from extensions import db
from datetime import datetime, timezone


class ProjectApplication(db.Model):
    __tablename__ = 'project_applications'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'))
    proposal = db.Column(db.Text)
    bid_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(50), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'freelancer_id': self.freelancer_id,
            'proposal': self.proposal,
            'bid_amount': float(self.bid_amount) if self.bid_amount else None,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }
