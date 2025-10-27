from .deliverable import Deliverable
from .invoice import Invoice
from .message import Message
from .milestone import Milestone
from .payment import Payment
from .project_application import ProjectApplication
from .project import Project
from .review import Review
from .skill import Skill, FreelancerSkill
from .time_log import TimeLog

# Alias for backward compatibility
TimeEntry = TimeLog
from .user import User, FreelancerProfile, ClientProfile

# Import from models.py for backward compatibility
try:
    from ..models import Application, Job
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