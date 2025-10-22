from app import create_app
from datetime import datetime,timezone,timedelta
from config import DevConfig
from extensions import db
from models import (
    User, Skill, ClientProfile, FreelancerProfile,FreelancerSkill,
    Project, Milestone, Invoice, Payment, ProjectApplication,
    TimeLog, Deliverable, Review, Message
)

def seed_data():
    app = create_app(DevConfig)
    with app.app_context():
        try:
            # Skills
            skill_names = ['Python', 'JavaScript', 'React', 'SQL', 'UI/UX Design', 'Node.js']

            # Query existing names
            existing = {s.name for s in db.session.query(Skill).filter(Skill.name.in_(skill_names)).all()}

            # Create only missing skills
            to_create = [Skill(name=name) for name in skill_names if name not in existing]
            if to_create:
                db.session.add_all(to_create)
                db.session.commit()

            # Users with proper password hashing
            users = {
                'client': User(
                    email='client@example.com',
                    role='client',
                    is_verified=True,
                    created_at=datetime.now(timezone.utc)
                ),
                'freelancer': User(
                    email='freelancer@example.com',
                    role='freelancer',
                    is_verified=True,
                    created_at=datetime.now(timezone.utc)
                )
            }
            for user in users.values():
                user.set_password('password123')  # Using proper password hashing
            db.session.add_all(users.values())
            db.session.commit()

            # Profiles
            client_profile = ClientProfile(
                user_id=users['client'].id,
                company_name='Acme Corp',
                industry='Technology',
                bio='Innovative tech solutions provider',
                website='https://acme.example.com',
                profile_picture_uri='https://acme.example.com/logo.png',
                created_at=datetime.now(timezone.utc)
            )
            freelancer_profile = FreelancerProfile(
                user_id=users['freelancer'].id,
                hourly_rate=50.00,
                bio='Full stack developer specializing in Python and React',
                experience='5 years freelance experience',
                portfolio_links='["https://portfolio.example.com", "https://github.com/example"]',
                profile_picture_uri='https://portfolio.example.com/profile.jpg',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add_all([client_profile, freelancer_profile])
            db.session.commit()

            # Freelancer skills
            skill_dict = {skill.name: skill for skill in db.session.query(Skill).all()}
            freelancer_skills = [
                FreelancerSkill(
                    freelancer_profile_id=freelancer_profile.id,
                    skill_id=skill_dict[name].id
                )
                for name in ['Python', 'React', 'JavaScript']
            ]
            db.session.add_all(freelancer_skills)
            db.session.commit()

            # Project
            project = Project(
                title='Website Development',
                description='Develop a responsive company website',
                budget=5000.00,
                status='in_progress',  # Using correct enum value
                client_id=client_profile.id,
                freelancer_id=freelancer_profile.id,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(project)
            db.session.commit()

            # Project Application (showing how freelancer was selected)
            application = ProjectApplication(
                project_id=project.id,
                freelancer_id=freelancer_profile.id,
                status='accepted',
                applied_at=datetime.now(timezone.utc) - timedelta(days=5)
            )
            db.session.add(application)
            db.session.commit()

            # Milestones with Deliverables and Invoices
            milestones = [
                Milestone(
                    project_id=project.id,
                    title='Design Phase',
                    description='Complete UI/UX design',
                    due_date=datetime.now(timezone.utc) + timedelta(days=25),
                    amount=1500.00,
                    status='in_progress'
                ),
                Milestone(
                    project_id=project.id,
                    title='Development Phase',
                    description='Build website frontend and backend',
                    due_date=datetime.now(timezone.utc) + timedelta(days=70),
                    amount=3500.00,
                    status='pending'
                )
            ]
            db.session.add_all(milestones)
            db.session.commit()

            # First milestone's deliverable
            deliverable = Deliverable(
                milestone_id=milestones[0].id,
                file_url='https://example.com/files/design-draft.pdf',
                link='https://figma.com/design/draft',
                submitted_at=datetime.now(timezone.utc),
                status='under_review'
            )
            db.session.add(deliverable)
            db.session.commit()

            # Invoice for first milestone
            invoice = Invoice(
                milestone_id=milestones[0].id,
                amount=1500.00,
                generated_at=datetime.now(timezone.utc),
                status='pending'
            )
            db.session.add(invoice)
            db.session.commit()

            # Payment for the invoice
            payment = Payment(
                invoice_id=invoice.id,
                client_id=client_profile.id,
                transaction_id='txn_123456',
                amount=1500.00,
                paid_at=datetime.now(timezone.utc),
                status='completed'
            )
            db.session.add(payment)
            db.session.commit()

            # Time logs
            time_logs = [
                TimeLog(
                    project_id=project.id,
                    freelancer_id=freelancer_profile.id,
                    start_time=datetime.now(timezone.utc) - timedelta(days=1, hours=4),
                    end_time=datetime.now(timezone.utc) - timedelta(days=1)
                ),
                TimeLog(
                    project_id=project.id,
                    freelancer_id=freelancer_profile.id,
                    start_time=datetime.now(timezone.utc) - timedelta(hours=5),
                    end_time=datetime.now(timezone.utc) - timedelta(hours=1)
                )
            ]
            db.session.add_all(time_logs)
            db.session.commit()

            # Messages
            messages = [
                Message(
                    project_id=project.id,
                    sender_id=users['client'].id,
                    receiver_id=users['freelancer'].id,
                    content='Can we schedule a progress review?',
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=24),
                    is_approved=True
                ),
                Message(
                    project_id=project.id,
                    sender_id=users['freelancer'].id,
                    receiver_id=users['client'].id,
                    content='Sure! I can show you the design progress tomorrow.',
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=23),
                    is_approved=True
                )
            ]
            db.session.add_all(messages)
            db.session.commit()

            # Initial project review
            review = Review(
                project_id=project.id,
                reviewer_id=users['client'].id,
                rating=4,
                comment='Great progress on the design phase!',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(review)
            db.session.commit()

            print("Seed data inserted successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"Error seeding data: {str(e)}")
            raise
        finally:
            db.session.close()

if __name__ == '__main__':
    seed_data()
