from src.extensions import db, ma
from datetime import datetime, timezone

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    budget = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client_profiles.id'))
    freelancer_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    client = db.relationship('ClientProfile', backref=db.backref('projects', lazy='dynamic'))
    freelancer = db.relationship('FreelancerProfile', backref=db.backref('projects', lazy='dynamic'))

class ProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        include_fk = True
        include_relationships = True

    # Convert decimal to float
    budget = ma.Float()
    
    # Add nested fields
    client_details = ma.Method('get_client_details', dump_only=True)
    freelancer_details = ma.Method('get_freelancer_details', dump_only=True)
    
    def get_client_details(self, obj):
        if obj.client:
            return {
                'id': obj.client.id,
                'company_name': obj.client.company_name,
                'industry': obj.client.industry
            }
        return None
        
    def get_freelancer_details(self, obj):
        if obj.freelancer:
            return {
                'id': obj.freelancer.id,
                'hourly_rate': float(obj.freelancer.hourly_rate) if obj.freelancer.hourly_rate else None
            }
        return None