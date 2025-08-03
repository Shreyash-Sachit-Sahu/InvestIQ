from app import db
from datetime import datetime
import json

class Recommendation(db.Model):
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preferences = db.Column(db.JSON, nullable=False)
    recommendations = db.Column(db.JSON, nullable=False)
    model_version = db.Column(db.String(50))
    confidence_score = db.Column(db.Numeric(5, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'preferences': self.preferences,
            'recommendations': self.recommendations,
            'modelVersion': self.model_version,
            'confidenceScore': float(self.confidence_score) if self.confidence_score else None,
            'createdAt': self.created_at.isoformat()
        }
