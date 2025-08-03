from app import db
from app.models.recommendation import Recommendation
from app.models.user import User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        pass
    
    def save_recommendation(self, user_id, preferences, recommendations, model_version="v2.1.0"):
        """Save recommendation to database"""
        try:
            # Calculate confidence score based on portfolio quality
            confidence_score = self._calculate_confidence_score(recommendations)
            
            recommendation = Recommendation(
                user_id=user_id,
                preferences=preferences,
                recommendations=recommendations,
                model_version=model_version,
                confidence_score=confidence_score
            )
            
            db.session.add(recommendation)
            db.session.commit()
            
            return recommendation.id
            
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
            db.session.rollback()
            return None
    
    def get_user_recommendations(self, user_id, limit=10):
        """Get user's recommendation history"""
        try:
            recommendations = Recommendation.query.filter_by(user_id=user_id)\
                .order_by(Recommendation.created_at.desc())\
                .limit(limit).all()
            
            return [rec.to_dict() for rec in recommendations]
            
        except Exception as e:
            logger.error(f"Error getting user recommendations: {e}")
            return []
    
    def get_recommendation_stats(self, user_id, days=30):
        """Get recommendation statistics for user"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            stats = db.session.query(
                db.func.count(Recommendation.id).label('total_recommendations'),
                db.func.avg(Recommendation.confidence_score).label('avg_confidence'),
                db.func.max(Recommendation.created_at).label('last_recommendation')
            ).filter(
                Recommendation.user_id == user_id,
                Recommendation.created_at >= since_date
            ).first()
            
            return {
                'total_recommendations': stats.total_recommendations or 0,
                'average_confidence': float(stats.avg_confidence or 0),
                'last_recommendation': stats.last_recommendation.isoformat() if stats.last_recommendation else None
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation stats: {e}")
            return {
                'total_recommendations': 0,
                'average_confidence': 0,
                'last_recommendation': None
            }
    
    def _calculate_confidence_score(self, recommendations):
        """Calculate confidence score for recommendations"""
        try:
            portfolio = recommendations.get('portfolio', [])
            summary = recommendations.get('summary', {})
            
            if not portfolio:
                return 50.0
            
            # Base confidence on diversification and expected returns
            diversification_score = summary.get('diversificationScore', 5)
            expected_return = summary.get('totalExpectedReturn', 10)
            
            # Calculate confidence (0-100)
            confidence = 50  # Base confidence
            confidence += (diversification_score - 5) * 5  # +/- 25 points for diversification
            confidence += min(max((expected_return - 10) * 2, -20), 20)  # +/- 20 points for returns
            
            return max(30, min(95, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 75.0
