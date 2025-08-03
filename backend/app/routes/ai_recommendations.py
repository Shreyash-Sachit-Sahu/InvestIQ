from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.recommendation import Recommendation
from app.utils.validators import validate_user_preferences
import logging

logger = logging.getLogger(__name__)

ai_recommendations_bp = Blueprint('ai_recommendations', __name__)

@ai_recommendations_bp.route('/recommend-nse', methods=['POST'])
@jwt_required()
def recommend_nse():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No preferences provided'
            }), 400
        
        # Validate user preferences
        if not validate_user_preferences(data):
            return jsonify({
                'success': False,
                'message': 'Invalid user preferences format'
            }), 400
        
        # Generate AI recommendations
        recommendations = current_app.ml_service.generate_ai_recommendations(data)
        
        if not recommendations:
            return jsonify({
                'success': False,
                'message': 'Failed to generate recommendations'
            }), 500
        
        # Save recommendations to database
        try:
            rec_record = Recommendation(
                user_id=user_id,
                preferences=data,
                recommendations=recommendations,
                model_version=recommendations.get('metadata', {}).get('modelVersion', 'v1.0.0'),
                confidence_score=85.0  # Default confidence score
            )
            
            db.session.add(rec_record)
            db.session.commit()
            
            # Add recommendation ID to metadata
            recommendations['metadata']['recommendationId'] = rec_record.id
            recommendations['metadata']['userId'] = f'user_{user_id}'
            
        except Exception as e:
            logger.warning(f"Failed to save recommendation to database: {e}")
            # Continue without saving to database
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'message': 'AI recommendations generated successfully'
        })
        
    except Exception as e:
        logger.error(f"AI recommendation error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to generate AI recommendations',
            'data': {
                'portfolio': [],
                'summary': {
                    'totalExpectedReturn': 0,
                    'portfolioRiskScore': 0,
                    'diversificationScore': 0,
                    'alignmentScore': 0
                },
                'insights': [],
                'metadata': {}
            }
        }), 500

@ai_recommendations_bp.route('/recommendations/history', methods=['GET'])
@jwt_required()
def get_recommendations_history():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Query recommendations
        recommendations = Recommendation.query.filter_by(user_id=user_id)\
            .order_by(Recommendation.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': [rec.to_dict() for rec in recommendations.items],
                'pagination': {
                    'page': page,
                    'pages': recommendations.pages,
                    'per_page': per_page,
                    'total': recommendations.total
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Get recommendations history error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch recommendations history'
        }), 500

@ai_recommendations_bp.route('/recommendations/<int:recommendation_id>', methods=['GET'])
@jwt_required()
def get_recommendation(recommendation_id):
    try:
        user_id = get_jwt_identity()
        
        recommendation = Recommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()
        
        if not recommendation:
            return jsonify({
                'success': False,
                'message': 'Recommendation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': recommendation.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get recommendation error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch recommendation'
        }), 500
