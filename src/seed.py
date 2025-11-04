from src.app import create_app
from src.extensions import db
from src.models import User, ClientProfile, FreelancerProfile, Project, Milestone, Deliverable, Invoice, Payment, Message, Review, Skill, FreelancerSkill, TimeLog, Dispute, Policy
from datetime import datetime, timezone, timedelta
import os
import random

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

    # Create an admin user
    admin_user = User(email='admin@example.com', role='admin')
    admin_user.set_password('adminpass')
    db.session.add(admin_user)
    db.session.commit()

    # Seed Skills and Policy
    skills = [Skill(name='Python'), Skill(name='JavaScript'), Skill(name='React'), Skill(name='Django')]
    db.session.add_all(skills)
    db.session.add(Policy(name='Payment Policy', content='Payments are due within 30 days'))
    db.session.commit()

    # Seed 70 users and their profiles (mix of clients and freelancers)
    client_profiles = []
    freelancer_profiles = []
    for i in range(1, 71):
        role = 'client' if i % 2 == 0 else 'freelancer'
        user = User(email=f'user{i}@example.com', role=role)
        user.set_password(f'pass{i}')
        db.session.add(user)
        db.session.flush()  # get id without committing

        if role == 'client':
            cp = ClientProfile(user_id=user.id, company_name=f'ClientCo{i}', industry='Tech')
            db.session.add(cp)
            client_profiles.append(cp)
        else:
            fp = FreelancerProfile(user_id=user.id, hourly_rate=random.randint(20, 100), bio=f'Freelancer {i}')
            db.session.add(fp)
            freelancer_profiles.append(fp)

        # commit every 10 users to avoid large transactions
        if i % 10 == 0:
            db.session.commit()

    db.session.commit()

    # Ensure we have at least one client and one freelancer
    if not client_profiles or not freelancer_profiles:
        raise RuntimeError('Need at least one client and one freelancer to create projects')

    # Seed 70 projects, each with a milestone and a dispute
    projects = []
    for i in range(1, 71):
        client = random.choice(client_profiles)
        freelancer = random.choice(freelancer_profiles)
        proj = Project(
            title=f'Project {i}',
            description=f'Description for project {i}',
            budget=round(random.uniform(100.0, 10000.0), 2),
            status=random.choice(['active', 'pending', 'completed']),
            client_id=client.id,
            freelancer_id=freelancer.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
        )
        db.session.add(proj)
        db.session.flush()
        # one milestone per project
        m = Milestone(
            project_id=proj.id,
            title=f'Milestone 1 for project {i}',
            description='Auto-generated milestone',
            due_date=datetime.now(timezone.utc) + timedelta(days=random.randint(1, 30)),
            amount=round(random.uniform(50.0, proj.budget or 1000.0), 2),
            status=random.choice(['pending', 'submitted', 'approved'])
        )
        db.session.add(m)
        db.session.flush()

        # dispute for this milestone
        d = Dispute(
            milestone_id=m.id,
            description=f'Auto-generated dispute for project {i}',
            status=random.choice(['open', 'pending', 'resolved'])
        )
        db.session.add(d)

        # commit periodically
        if i % 10 == 0:
            db.session.commit()

    db.session.commit()

    print("Database seeded successfully with 70 users, 70 projects and 70 disputes!")
