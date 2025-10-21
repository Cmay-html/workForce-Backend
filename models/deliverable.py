from extensions import db
from datetime import datetime, timezone


class Deliverable(db.Model):
    __tablename__ = 'deliverables'

    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'))
    file_url = db.Column(db.String(255))
    link = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'milestone_id': self.milestone_id,
            'file_url': self.file_url,
            'link': self.link,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'status': self.status
        }
