from app import create_app
from models import Project, ProjectSchema
from flask import jsonify

app = create_app()

with app.app_context():
    try:
        # Test Project Query
        projects = Project.query.all()
        
        # Try to serialize a project
        project_schema = ProjectSchema()
        result = project_schema.dump(projects[0])
        print("\nSerialized Project:")
        print(result)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        print(traceback.format_exc())