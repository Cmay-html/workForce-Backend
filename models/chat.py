from ..extensions import db
from datetime import datetime

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # 'text', 'file', 'system'
    file_url = db.Column(db.String(255))  # For file attachments
    file_name = db.Column(db.String(255))  # Original file name
    file_size = db.Column(db.Integer)  # File size in bytes
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', backref='chat_messages', lazy=True)
    sender = db.relationship('User', backref='sent_messages', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.first_name + ' ' + self.sender.last_name if self.sender.first_name and self.sender.last_name else self.sender.username,
            'sender_role': self.sender.role,
            'message': self.message,
            'message_type': self.message_type,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }