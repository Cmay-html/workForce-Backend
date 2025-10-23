from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User

# Create namespace
api = Namespace('freelancer', description='Freelancer operations')

# API models for Swagger documentation
freelancer_model = api.model('Freelancer', {
    'id': fields.Integer(readonly=True, description='Freelancer ID'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'email': fields.String(required=True, description='Email'),
    'role': fields.String(description='User role'),
    'created_at': fields.String(description='Creation date')
})

@api.route('/profile')
class FreelancerProfile(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @jwt_required()
    def get(self):
        """Get freelancer profile"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get_or_404(current_user_id)

            return {
                'success': True,
                'data': user.to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching profile: {str(e)}'
            }, 500
