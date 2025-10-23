# routes/role1/reviews.py
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Review, Project, User

# Create namespace
api = Namespace('reviews', description='Review operations')

# API models for Swagger documentation
review_model = api.model('Review', {
    'id': fields.Integer(readonly=True, description='Review ID'),
    'project_id': fields.Integer(required=True, description='Project ID'),
    'reviewer_id': fields.Integer(readonly=True, description='Reviewer ID'),
    'rating': fields.Integer(required=True, description='Rating (1-5)'),
    'comment': fields.String(required=True, description='Review comment'),
    'created_at': fields.String(description='Creation date')
})

review_create_model = api.model('ReviewCreate', {
    'project_id': fields.Integer(required=True, description='Project ID'),
    'rating': fields.Integer(required=True, description='Rating (1-5)'),
    'comment': fields.String(required=True, description='Review comment')
})


@api.route('/')
class ReviewList(Resource):
    @api.doc(security='Bearer Auth')
    @api.expect(review_create_model)
    @api.response(201, 'Review created successfully')
    @api.response(400, 'Validation error')
    @api.response(403, 'Forbidden')
    @jwt_required()
    def post(self):
        """Create a review for a freelancer (client perspective)"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()

            # Validate required fields
            required_fields = ['project_id', 'rating', 'comment']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'{field} is required'
                    }, 400

            project_id = data['project_id']
            rating = data['rating']
            comment = data['comment']

            # Validate rating range
            if rating < 1 or rating > 5:
                return {
                    'success': False,
                    'message': 'Rating must be between 1 and 5'
                }, 400

            # Verify project exists and user is the client
            project = Project.query.get(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found'
                }, 404

            if project.client_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Only the project client can create reviews'
                }, 403

            # Check if project is completed
            if project.status != 'completed':
                return {
                    'success': False,
                    'message': 'Can only review completed projects'
                }, 400

            # Check if freelancer is assigned
            if not project.freelancer_id:
                return {
                    'success': False,
                    'message': 'No freelancer assigned to this project'
                }, 400

            # Check if review already exists for this project from this client
            existing_review = Review.query.filter_by(
                project_id=project_id,
                reviewer_id=current_user_id
            ).first()

            if existing_review:
                return {
                    'success': False,
                    'message': 'You have already reviewed this project'
                }, 400

            # Create review
            review = Review(
                project_id=project_id,
                reviewer_id=current_user_id,
                rating=rating,
                comment=comment
            )

            db.session.add(review)
            db.session.commit()

            return {
                'success': True,
                'data': review.to_dict(),
                'message': 'Review submitted successfully'
            }, 201

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error creating review: {str(e)}'
            }, 400

    @api.doc(security='Bearer Auth', params={
        'page': 'Page number',
        'per_page': 'Items per page',
        'project_id': 'Filter by project ID'
    })
    @api.response(200, 'Success')
    @api.response(401, 'Unauthorized')
    @jwt_required()
    def get(self):
        """Get reviews written by the current client"""
        try:
            current_user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            project_id = request.args.get('project_id', type=int)

            # Build query
            query = Review.query.filter_by(reviewer_id=current_user_id)

            # Filter by project if provided
            if project_id:
                query = query.filter_by(project_id=project_id)

            reviews = query.order_by(Review.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)

            # Get project and freelancer details for each review
            reviews_data = []
            for review in reviews.items:
                project = Project.query.get(review.project_id)
                freelancer = User.query.get(
                    project.freelancer_id) if project else None

                reviews_data.append({
                    **review.to_dict(),
                    'project_title': project.title if project else 'Unknown Project',
                    'freelancer_name': f"{freelancer.first_name} {freelancer.last_name}" if freelancer else 'Unknown Freelancer',
                    'freelancer_id': project.freelancer_id if project else None
                })

            return {
                'success': True,
                'data': reviews_data,
                'pagination': {
                    'page': reviews.page,
                    'per_page': reviews.per_page,
                    'total': reviews.total,
                    'pages': reviews.pages
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching reviews: {str(e)}'
            }, 500


@api.route('/<int:review_id>')
class ReviewResource(Resource):
    @api.doc(security='Bearer Auth')
    @api.response(200, 'Success')
    @api.response(404, 'Review not found')
    @jwt_required()
    def get(self, review_id):
        """Get a specific review"""
        try:
            current_user_id = get_jwt_identity()
            review = Review.query.get_or_404(review_id)

            # Check if user is the reviewer
            if review.reviewer_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to view this review'
                }, 403

            # Get additional details
            project = Project.query.get(review.project_id)
            freelancer = User.query.get(
                project.freelancer_id) if project else None

            review_data = {
                **review.to_dict(),
                'project_title': project.title if project else 'Unknown Project',
                'freelancer_name': f"{freelancer.first_name} {freelancer.last_name}" if freelancer else 'Unknown Freelancer',
                'freelancer_id': project.freelancer_id if project else None
            }

            return {
                'success': True,
                'data': review_data
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching review: {str(e)}'
            }, 500

    @api.doc(security='Bearer Auth')
    @api.expect(review_create_model)
    @api.response(200, 'Review updated successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Review not found')
    @jwt_required()
    def put(self, review_id):
        """Update a review"""
        try:
            current_user_id = get_jwt_identity()
            review = Review.query.get_or_404(review_id)
            data = request.get_json()

            # Check if user is the reviewer
            if review.reviewer_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to update this review'
                }, 403

            # Update fields if provided
            if 'rating' in data:
                rating = data['rating']
                if rating < 1 or rating > 5:
                    return {
                        'success': False,
                        'message': 'Rating must be between 1 and 5'
                    }, 400
                review.rating = rating

            if 'comment' in data:
                review.comment = data['comment']

            db.session.commit()

            return {
                'success': True,
                'data': review.to_dict(),
                'message': 'Review updated successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error updating review: {str(e)}'
            }, 400

    @api.doc(security='Bearer Auth')
    @api.response(200, 'Review deleted successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Review not found')
    @jwt_required()
    def delete(self, review_id):
        """Delete a review"""
        try:
            current_user_id = get_jwt_identity()
            review = Review.query.get_or_404(review_id)

            # Check if user is the reviewer
            if review.reviewer_id != current_user_id:
                return {
                    'success': False,
                    'message': 'Not authorized to delete this review'
                }, 403

            db.session.delete(review)
            db.session.commit()

            return {
                'success': True,
                'message': 'Review deleted successfully'
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error deleting review: {str(e)}'
            }, 400


@api.route('/freelancer/<int:freelancer_id>')
class FreelancerReviews(Resource):
    @api.doc(security='Bearer Auth', params={
        'page': 'Page number',
        'per_page': 'Items per page'
    })
    @api.response(200, 'Success')
    @api.response(404, 'Freelancer not found')
    @jwt_required()
    def get(self, freelancer_id):
        """Get all reviews for a specific freelancer"""
        try:
            # Verify freelancer exists
            freelancer = User.query.get(freelancer_id)
            if not freelancer:
                return {
                    'success': False,
                    'message': 'Freelancer not found'
                }, 404

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # Get projects where this freelancer was hired
            projects = Project.query.filter_by(
                freelancer_id=freelancer_id).all()
            project_ids = [project.id for project in projects]

            if not project_ids:
                return {
                    'success': True,
                    'data': [],
                    'pagination': {
                        'page': 1,
                        'per_page': per_page,
                        'total': 0,
                        'pages': 0
                    }
                }

            # Get reviews for these projects
            reviews = Review.query.filter(Review.project_id.in_(project_ids))\
                .join(User, Review.reviewer_id == User.id)\
                .add_entity(User)\
                .order_by(Review.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)

            reviews_data = []
            for review_pair in reviews.items:
                review, reviewer = review_pair
                project = Project.query.get(review.project_id)

                reviews_data.append({
                    **review.to_dict(),
                    'reviewer_name': f"{reviewer.first_name} {reviewer.last_name}",
                    'project_title': project.title if project else 'Unknown Project'
                })

            return {
                'success': True,
                'data': reviews_data,
                'pagination': {
                    'page': reviews.page,
                    'per_page': reviews.per_page,
                    'total': reviews.total,
                    'pages': reviews.pages
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error fetching freelancer reviews: {str(e)}'
            }, 500
