from app import create_app
from extensions import db
from models import Project, ClientProfile, FreelancerProfile

app = create_app()

with app.app_context():
    try:
        # Test Project Query
        projects = Project.query.all()
        print(f"\nTotal Projects: {len(projects)}")
        
        if projects:
            project = projects[0]
            print(f"\nFirst Project:")
            print(f"Title: {project.title}")
            print(f"Client ID: {project.client_id}")
            print(f"Freelancer ID: {project.freelancer_id}")
            
            # Test relationships
            if project.client:
                print(f"Client Company: {project.client.company_name}")
            else:
                print("No client associated")
                
            if project.freelancer:
                print(f"Freelancer ID: {project.freelancer.id}")
            else:
                print("No freelancer associated")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        print(traceback.format_exc())