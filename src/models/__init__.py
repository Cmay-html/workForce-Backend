# models/__init__.py
from ..extensions import db

# Import all models first (without schemas)
from .skill import Skill, FreelancerSkill
from .user import User, ClientProfile, FreelancerProfile
from .project import Project
from .milestone import Milestone
from .dispute import Dispute
from .deliverable import Deliverable
from .invoice import Invoice
from .payment import Payment
from .message import Message
from .review import Review
# skill already imported above
from .time_log import TimeLog
from .project_application import ProjectApplication
from .policy import Policy

# Import schemas
from .user import UserSchema, ClientProfileSchema, FreelancerProfileSchema
from .project import ProjectSchema
from .milestone import MilestoneSchema
from .dispute import DisputeSchema
from .deliverable import DeliverableSchema
from .invoice import InvoiceSchema
from .payment import PaymentSchema
from .message import MessageSchema
from .review import ReviewSchema
from .skill import SkillSchema, FreelancerSkillSchema
from .time_log import TimeLogSchema
from .project_application import ProjectApplicationSchema
from .policy import PolicySchema

# Alias for backward compatibility
TimeEntry = TimeLog
from .user import User, FreelancerProfile, ClientProfile

# Import from models.py for backward compatibility
try:
    from models import Application, Job
except ImportError:
    # Fallback if models.py doesn't exist
    Application = None
    Job = None


__all__ = [
    'Deliverable',
    'Invoice',
    'Message',
    'Milestone',
    'Payment',
    'ProjectApplication',
    'Project',
    'Review',
    'Skill',
    'FreelancerSkill',
    'TimeLog',
    'TimeEntry',  # Alias
    'User',
    'FreelancerProfile',
    'ClientProfile',
    'Application',
    'Job',
]
