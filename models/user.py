# routes/freelancer_profile.py

from flask import request
from flask_restx import Namespace, Resource, fields
from extensions import db
from models import FreelancerProfile
from datetime import datetime, timezone

freelancer_ns = Namespace('freelancers', description='Freelancer Profile operations')

# -----------------------------
# RESTX Model
# -----------------------------
freelancer_model = freelancer_ns.model('FreelancerProfile', {
    'id': fields.Integer(readonly=True),
    'user_id': fields.Integer(required=True),
    'hourly_rate': fields.Float,
    'bio': fields.String,
    'experience': fields.String,
    'portfolio_links': fields.String,
    'profile_picture_uri': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
})

# -----------------------------
# Routes
# -----------------------------
@freelancer_ns.route('/')
class FreelancerList(Resource):
    @freelancer_ns.marshal_list_with(freelancer_model)
    def get(self):
        """Get all freelancer profiles"""
        return FreelancerProfile.query.all()

    @freelancer_ns.expect(freelancer_model, validate=True)
    @freelancer_ns.marshal_with(freelancer_model, code=201)
    def post(self):
        """Create a new freelancer profile"""
        data = request.json
        freelancer = FreelancerProfile(
            user_id=data['user_id'],
            hourly_rate=data.get('hourly_rate'),
            bio=data.get('bio'),
            experience=data.get('experience'),
            portfolio_links=data.get('portfolio_links'),
            profile_picture_uri=data.get('profile_picture_uri'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(freelancer)
        db.session.commit()
        return freelancer, 201

@freelancer_ns.route('/<int:id>')
@freelancer_ns.param('id', 'Freelancer Profile identifier')
class FreelancerResource(Resource):
    @freelancer_ns.marshal_with(freelancer_model)
    def get(self, id):
        """Get a specific freelancer profile"""
        return FreelancerProfile.query.get_or_404(id)

    @freelancer_ns.expect(freelancer_model, validate=True)
    @freelancer_ns.marshal_with(freelancer_model)
    def put(self, id):
        """Update a freelancer profile"""
        freelancer = FreelancerProfile.query.get_or_404(id)
        data = request.json

        freelancer.user_id = data.get('user_id', freelancer.user_id)
        freelancer.hourly_rate = data.get('hourly_rate', freelancer.hourly_rate)
        freelancer.bio = data.get('bio', freelancer.bio)
        freelancer.experience = data.get('experience', freelancer.experience)
        freelancer.portfolio_links = data.get('portfolio_links', freelancer.portfolio_links)
        freelancer.profile_picture_uri = data.get('profile_picture_uri', freelancer.profile_picture_uri)
        freelancer.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        return freelancer

    def delete(self, id):
        """Delete a freelancer profile"""
        freelancer = FreelancerProfile.query.get_or_404(id)
        db.session.delete(freelancer)
        db.session.commit()
        return {'message': f'Freelancer profile {id} deleted successfully'}, 200
