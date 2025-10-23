# app.py
from flask import Flask
from flask_restx import Api
from config import Config
from extensions import db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Create API instance
    api = Api(
        app,
        version='1.0',
        title='KaziFlow API',
        description='Freelance Platform API',
        doc='/swagger/',
        authorizations={
            'Bearer Auth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Enter: Bearer <your_jwt_token>'
            }
        }
    )

    # Register existing routes
    from routes.projects import api as projects_ns
    from routes.milestone import api as milestones_ns
    from routes.review import api as review_ns
    from routes.freelancer import api as freelancer_ns

    # Register namespaces with their paths
    api.add_namespace(projects_ns, path='/api/projects')
    api.add_namespace(milestones_ns, path='/api/milestones')
    api.add_namespace(review_ns, path='/api/reviews')
    api.add_namespace(freelancer_ns, path='/api/freelancer')

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)