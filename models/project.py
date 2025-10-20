from ..extensions import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'completed', 'cancelled'
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    category = db.Column(db.String(50))
    tags = db.Column(db.Text)  # JSON string or comma-separated

    # Relationships
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='project', lazy=True)
    payments = db.relationship('Payment', backref='project', lazy=True)
    project_chats = db.relationship('Chat', backref='chat_project', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'budget': self.budget,
            'status': self.status,
            'client_id': self.client_id,
            'freelancer_id': self.freelancer_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'category': self.category,
            'tags': self.tags
        }