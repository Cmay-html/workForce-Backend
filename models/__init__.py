from .deliverable import Deliverable, DeliverableSchema
from .invoice import Invoice, InvoiceSchema
from .message import Message, MessageSchema
from .milestone import Milestone, MilestoneSchema
from .payment import Payment, PaymentSchema
from .project_application import ProjectApplication, ProjectApplicationSchema
from .project import Project, ProjectSchema
from .review import Review, ReviewSchema
from .skill import Skill, SkillSchema, FreelancerSkill, FreelancerSkillSchema
from .time_log import TimeLog, TimeLogSchema
from .user import User, UserSchema, ClientProfile, ClientProfileSchema, FreelancerProfile, FreelancerProfileSchema
from .dispute import Dispute, DisputeSchema
from .policy import Policy, PolicySchema
from extensions import db

def setup_relationships():
    # Set up the TimeLog relationship for Project
    Project.time_logs = db.relationship('TimeLog', backref='project', lazy=True, cascade='all, delete-orphan')

# Call the setup function after all imports
setup_relationships()

__all__ = [
    'Deliverable', 'DeliverableSchema',
    'Invoice', 'InvoiceSchema',
    'Message', 'MessageSchema',
    'Milestone', 'MilestoneSchema',
    'Payment', 'PaymentSchema',
    'ProjectApplication', 'ProjectApplicationSchema',
    'Project', 'ProjectSchema',
    'Review', 'ReviewSchema',
    'Skill', 'SkillSchema',
    'FreelancerSkill', 'FreelancerSkillSchema',
    'TimeLog', 'TimeLogSchema',
    'User', 'UserSchema',
    'ClientProfile', 'ClientProfileSchema',
    'FreelancerProfile', 'FreelancerProfileSchema',
    'Dispute', 'DisputeSchema',
    'Policy', 'PolicySchema',
]