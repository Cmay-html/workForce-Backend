from extensions import db
from datetime import datetime, timezone
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    attachment_url = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean)

    # Define relationships
    project = db.relationship('Project', backref=db.backref('messages', cascade='all, delete-orphan'))
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'attachment_url': self.attachment_url,
            'is_approved': self.is_approved
        }

class MessageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        load_instance = True