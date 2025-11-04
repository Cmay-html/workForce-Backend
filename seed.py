# seed.py

from app import create_app
from extensions import db
from models import User, ClientProfile, FreelancerProfile, Project, Milestone, Deliverable, Invoice, Payment, Message, Review, Skill, FreelancerSkill, TimeLog, Dispute, Policy
from datetime import datetime, timezone, timedelta
import os

# Create app context
app = create_app()
with app.app_context():
    # Clear existing data in the correct order (dependent tables first)
    db.session.query(TimeLog).delete()
    db.session.query(FreelancerSkill).delete()
    db.session.query(Review).delete()
    db.session.query(Message).delete()
    db.session.query(Payment).delete()
    db.session.query(Invoice).delete()
    db.session.query(Deliverable).delete()
    
    # CORRECTED ORDER: Delete Disputes before Milestones
    db.session.query(Dispute).delete() 
    db.session.query(Milestone).delete()

    db.session.query(Project).delete()
    db.session.query(ClientProfile).delete()
    db.session.query(FreelancerProfile).delete()
    db.session.query(Skill).delete()
    db.session.query(Policy).delete()
    db.session.query(User).delete()  # Delete users last
    db.session.commit()

    # ... (the rest of your seeding code is perfectly fine) ...
    # Seed Users
    admin_user = User(email='admin@example.com', role='admin')
    admin_user.set_password('adminpass')
    client_user = User(email='client@example.com', role='client')
    client_user.set_password('clientpass')
    freelancer_user = User(email='freelancer@example.com', role='freelancer')
    freelancer_user.set_password('freelancerpass')
    db.session.add_all([admin_user, client_user, freelancer_user])
    db.session.commit()

    # Seed Profiles
    client_profile = ClientProfile(user_id=client_user.id, company_name='ClientCo', industry='Tech')
    freelancer_profile = FreelancerProfile(user_id=freelancer_user.id, hourly_rate=50.00, bio='Experienced developer')
    db.session.add_all([client_profile, freelancer_profile])
    db.session.commit()

    # Seed Skills
    skill1 = Skill(name='Python')
    skill2 = Skill(name='JavaScript')
    db.session.add_all([skill1, skill2])
    db.session.commit()

    # Seed Freelancer Skills
    freelancer_skill = FreelancerSkill(freelancer_profile_id=freelancer_profile.id, skill_id=skill1.id)
    db.session.add(freelancer_skill)
    db.session.commit()

    # Seed Project
    project = Project(
        title='Website Development',
        description='Build a responsive website',
        budget=1000.00,
        status='active',
        client_id=client_profile.id,
        freelancer_id=freelancer_profile.id,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(project)
    db.session.commit()

    # Seed Milestone
    milestone = Milestone(
        project_id=project.id,
        title='Design Phase',
        description='Complete website design',
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        amount=300.00,
        status='pending'
    )
    db.session.add(milestone)
    db.session.commit()

    # Seed Deliverable
    deliverable = Deliverable(
        milestone_id=milestone.id,
        file_url='http://example.com/design.pdf',
        status='submitted'
    )
    db.session.add(deliverable)
    db.session.commit()

    # Seed Invoice
    invoice = Invoice(milestone_id=milestone.id, amount=300.00, status='pending')
    db.session.add(invoice)
    db.session.commit()

    # Seed Payment
    payment = Payment(invoice_id=invoice.id, client_id=client_profile.id, amount=300.00, status='processed')
    db.session.add(payment)
    db.session.commit()

    # Seed Message
    message = Message(
        project_id=project.id,
        sender_id=freelancer_profile.user_id,
        receiver_id=client_profile.user_id,
        content='Design is ready for review',
        is_approved=False
    )
    db.session.add(message)
    db.session.commit()

    # Seed Review
    review = Review(
        project_id=project.id,
        reviewer_id=client_profile.user_id,
        rating=4,
        comment='Good work!'
    )
    db.session.add(review)
    db.session.commit()

    # Seed TimeLog
    time_log = TimeLog(
        project_id=project.id,
        freelancer_id=freelancer_profile.id,
        start_time=datetime.now(timezone.utc) - timedelta(hours=2),
        end_time=datetime.now(timezone.utc)
    )
    db.session.add(time_log)
    db.session.commit()

    # Seed Dispute
    dispute = Dispute(
        milestone_id=milestone.id,
        description='Delay in delivery',
        status='open'
    )
    db.session.add(dispute)
    db.session.commit()

    # Seed Policy
    policy = Policy(name='Payment Policy', content='Payments are due within 30 days')
    db.session.add(policy)
    db.session.commit()

    print("Database seeded successfully!")