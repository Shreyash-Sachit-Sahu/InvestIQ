from app.ml_models.stock_predictor import StockScoringModel
from app.ml_models.portfolio_optimizer import PortfolioOptimizer
from app.ml_models.risk_assessor import RiskAssessmentModel
from app.services.nse_data_service import NSEDataService
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.stock_scorer = StockScoringModel()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_assessor = RiskAssessmentModel()
        self.nse_data_service = NSEDataService()
        
        # Load pre-trained models if available
        self._load_models()
        
        # Initialize with sample data if needed
        self._initialize_service()
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
        
        try:
            stock_scorer_path = os.path.join(model_path, 'stock_scorer.pkl')
            if os.path.exists(stock_scorer_path):
                self.stock_scorer.load_model(stock_scorer_path)
                logger.info("Loaded pre-trained stock scoring model")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _initialize_service(self):
        """Initialize the ML service with training data"""
        try:
            # Get stock data for training
            stock_data = self.nse_data_service.get_all_stocks_data()
            
            if not stock_data:
                logger.warning("No stock data available, using synthetic data")
                stock_data = []
            
            # Train the stock scoring model
            self.stock_scorer.train(stock_data)
            logger.info(f"ML Service initialized with {len(stock_data)} stocks")
            
        except Exception as e:
            logger.error(f"Error initializing ML service: {e}")
            # Initialize with synthetic data
            self.stock_scorer.train([])
    
    def generate_ai_recommendations(self, user_preferences):
        """
        Generate AI-powered investment recommendations
        
        Args:
            user_preferences: Dictionary containing user investment preferences
        
        Returns:
            Dictionary with portfolio recommendations and analysis
        """
        try:
            start_time = datetime.now()
            
            # Get current stock data
            stock_data = self.nse_data_service.get_all_stocks_data()
            
            if not stock_data:
                logger.warning("No stock data available, using default portfolio")
                return self._get_default_recommendations(user_preferences)
            
            # Score all stocks
            logger.info(f"Scoring {len(stock_data)} stocks")
            stock_scores = self.stock_scorer.score_stocks(stock_data)
            
            # Optimize portfolio allocation
            logger.info("Optimizing portfolio allocation")
            portfolio = self.portfolio_optimizer.optimize_portfolio(
                stock_scores, user_preferences
            )
            
            # Assess portfolio risk
            logger.info("Assessing portfolio risk")
            risk_metrics = self.risk_assessor.assess_portfolio_risk(portfolio)
            
            # Calculate summary metrics
            summary = self._calculate_portfolio_summary(portfolio, risk_metrics)
            
            # Generate insights
            insights = self._generate_insights(portfolio, user_preferences, risk_metrics)
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Create response
            recommendations = {
                'portfolio': portfolio,
                'summary': summary,
                'insights': insights,
                'metadata': {
                    'generatedAt': datetime.now().isoformat() + 'Z',
                    'modelVersion': 'v2.1.0',
                    'dataSource': 'NSE',
                    'processingTime': processing_time,
                    'stocksAnalyzed': len(stock_data)
                }
            }
            
            logger.info(f"Generated recommendations in {processing_time}ms")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_default_recommendations(user_preferences)
    
    def _calculate_portfolio_summary(self, portfolio, risk_metrics):
        """Calculate portfolio summary metrics"""
        if not portfolio:
            return {
                'totalExpectedReturn': 10.0,
                'portfolioRiskScore': 3.0,
                'diversificationScore': 5,
                'alignmentScore': 70
            }
        
        # Calculate weighted expected return
        total_expected_return = 0
        total_weight = 0
        
        for holding in portfolio:
            weight = holding.get('allocation', 0) / 100
            expected_return = holding.get('expectedReturn', 10)
            total_expected_return += weight * expected_return
            total_weight += weight
        
        avg_expected_return = total_expected_return / total_weight if total_weight > 0 else 10.0
        
        # Calculate alignment score based on risk tolerance match
        portfolio_risk = risk_metrics.get('portfolioRiskScore', 3.0)
        target_risk = 3.0  # Default moderate risk
        risk_alignment = max(0, 100 - abs(portfolio_risk - target_risk) * 20)
        
        return {
            'totalExpectedReturn': round(avg_expected_return, 2),
            'portfolioRiskScore': risk_metrics.get('portfolioRiskScore', 3.0),
            'diversificationScore': risk_metrics.get('diversificationScore', 5),
            'alignmentScore': int(risk_alignment)
        }
    
    def _generate_insights(self, portfolio, user_preferences, risk_metrics):
        """Generate investment insights"""
        insights = []
        
        if not portfolio:
            return ['Unable to generate specific insights due to limited data availability.']
        
        # Risk tolerance alignment
        portfolio_risk = risk_metrics.get('portfolioRiskScore', 3.0)
        risk_tolerance = user_preferences.get('risk_tolerance', 2)
        
        if risk_tolerance == 1 and portfolio_risk <= 2.5:
            insights.append('Portfolio aligns well with your conservative risk tolerance with focus on stable, dividend-paying stocks.')
        elif risk_tolerance == 2 and 2.0 <= portfolio_risk <= 3.5:
            insights.append('Portfolio matches your moderate risk tolerance with balanced growth and stability.')
        elif risk_tolerance == 3 and portfolio_risk >= 3.0:
            insights.append('Portfolio suits your aggressive risk tolerance with growth-oriented stock selection.')
        else:
            insights.append('Portfolio risk level may not perfectly match your stated risk tolerance - consider adjusting allocations.')
        
        # Diversification insights
        diversification = risk_metrics.get('diversificationScore', 5)
        if diversification >= 8:
            insights.append('Excellent diversification across multiple sectors reduces portfolio concentration risk.')
        elif diversification >= 6:
            insights.append('Good diversification provides reasonable risk reduction while maintaining growth potential.')
        else:
            insights.append('Consider adding more stocks from different sectors to improve diversification.')
        
        # Sector concentration
        sectors = {}
        for holding in portfolio:
            sector = holding.get('sector', 'Other')
            allocation = holding.get('allocation', 0)
            sectors[sector] = sectors.get(sector, 0) + allocation
        
        max_sector_allocation = max(sectors.values()) if sectors else 0
        if max_sector_allocation > 40:
            dominant_sector = max(sectors.keys(), key=lambda k: sectors[k])
            insights.append(f'High concentration in {dominant_sector} sector - monitor for sector-specific risks.')
        
        # Expected returns insight
        summary = self._calculate_portfolio_summary(portfolio, risk_metrics)
        expected_return = summary.get('totalExpectedReturn', 10)
        if expected_return > 15:
            insights.append('Portfolio targets above-average returns but comes with correspondingly higher risk.')
        elif expected_return < 10:
            insights.append('Conservative return expectations align with lower-risk investment approach.')
        
        return insights[:4]  # Return maximum 4 insights
    
    def _get_default_recommendations(self, user_preferences):
        """Return default recommendations when data is not available"""
        default_portfolio = [
            {
                'symbol': 'RELIANCE',
                'name': 'Reliance Industries Ltd',
                'allocation': 25.0,
                'confidence': 87,
                'reasoning': 'Market leader with diversified business model across energy and digital services',
                'sector': 'Energy',
                'expectedReturn': 12.5,
                'riskScore': 4,
                'currentPrice': 2456.30,
                'marketCap': 1658420,
                'pe': 15.2,
                'dividend': 2.1
            },
            {
                'symbol': 'TCS',
                'name': 'Tata Consultancy Services',
                'allocation': 20.0,
                'confidence': 89,
                'reasoning': 'Leading IT services company with strong global presence and consistent growth',
                'sector': 'Information Technology',
                'expectedReturn': 14.2,
                'riskScore': 3,
                'currentPrice': 3245.60,
                'marketCap': 1235680,
                'pe': 22.5,
                'dividend': 1.8
            },
            {
                'symbol': 'HDFCBANK',
                'name': 'HDFC Bank Limited',
                'allocation': 18.0,
                'confidence': 85,
                'reasoning': 'Premier private bank with strong fundamentals and consistent performance',
                'sector': 'Financial Services',
                'expectedReturn': 13.8,
                'riskScore': 3,
                'currentPrice': 1678.45,
                'marketCap': 1278950,
                'pe': 18.7,
                'dividend': 1.5
            },
            {
                'symbol': 'INFY',
                'name': 'Infosys Limited',
                'allocation': 15.0,
                'confidence': 82,
                'reasoning': 'Global IT services leader with strong digital transformation capabilities',
                'sector': 'Information Technology',
                'expectedReturn': 13.5,
                'riskScore': 3,
                'currentPrice': 1456.80,
                'marketCap': 612340,
                'pe': 24.3,
                'dividend': 2.5
            },
            {
                'symbol': 'ITC',
                'name': 'ITC Limited',
                'allocation': 12.0,
                'confidence': 78,
                'reasoning': 'Diversified conglomerate with stable cash flows and strong brand portfolio',
                'sector': 'Consumer Goods',
                'expectedReturn': 11.8,
                'riskScore': 2,
                'currentPrice': 412.60,
                'marketCap': 512890,
                'pe': 28.4,
                'dividend': 5.2
            },
            {
                'symbol': 'HINDUNILVR',
                'name': 'Hindustan Unilever Ltd',
                'allocation': 10.0,
                'confidence': 80,
                'reasoning': 'Leading FMCG company with strong rural presence and brand portfolio',
                'sector': 'Consumer Goods',
                'expectedReturn': 12.2,
                'riskScore': 2,
                'currentPrice': 2567.30,
                'marketCap': 602150,
                'pe': 56.8,
                'dividend': 1.8
            }
        ]
        
        return {
            'portfolio': default_portfolio,
            'summary': {
                'totalExpectedReturn': 13.42,
                'portfolioRiskScore': 3.0,
                'diversificationScore': 8,
                'alignmentScore': 89
            },
            'insights': [
                'Portfolio provides excellent diversification across 4 major sectors',
                'Balanced mix of growth and value stocks suitable for moderate risk tolerance',
                'Strong focus on market leaders with proven track records',
                'Expected returns balanced with reasonable risk levels'
            ],
            'metadata': {
                'generatedAt': datetime.now().isoformat() + 'Z',
                'modelVersion': 'v2.1.0',
                'dataSource': 'Default',
                'processingTime': 100,
                'stocksAnalyzed': 0
            }
        }
    
    def save_models(self):
        """Save trained models to disk"""
        try:
            model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
            os.makedirs(model_path, exist_ok=True)
            
            # Save stock scoring model
            stock_scorer_path = os.path.join(model_path, 'stock_scorer.pkl')
            self.stock_scorer.save_model(stock_scorer_path)
            
            logger.info("Models saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
