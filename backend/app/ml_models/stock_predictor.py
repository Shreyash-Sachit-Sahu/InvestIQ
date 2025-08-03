import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

class StockScoringModel:
    def __init__(self):
        self.fundamental_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.technical_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, stock_data):
        """Prepare features for stock scoring"""
        features = []
        
        for stock in stock_data:
            feature_vector = [
                stock.get('pe_ratio', 15.0) or 15.0,
                stock.get('dividend_yield', 2.0) or 2.0,
                stock.get('beta', 1.0) or 1.0,
                stock.get('market_cap', 100000) / 1000000,  # Normalize to millions
                self._calculate_momentum_score(stock),
                self._calculate_quality_score(stock),
                self._calculate_value_score(stock),
                self._get_sector_score(stock.get('sector', 'Other'))
            ]
            features.append(feature_vector)
            
        return np.array(features)
    
    def _calculate_momentum_score(self, stock):
        """Calculate momentum score based on price performance"""
        # Simplified momentum calculation
        price = stock.get('current_price', 100)
        return min(max((price - 100) / 100, -1), 1)  # Normalize between -1 and 1
    
    def _calculate_quality_score(self, stock):
        """Calculate quality score based on fundamentals"""
        pe = stock.get('pe_ratio', 15) or 15
        # Lower PE generally indicates better value (inverted scoring)
        return max(0, (30 - pe) / 30)  # Normalize 0-1
    
    def _calculate_value_score(self, stock):
        """Calculate value score"""
        pe = stock.get('pe_ratio', 15) or 15
        dividend = stock.get('dividend_yield', 2) or 2
        return (dividend / 5) + max(0, (25 - pe) / 25)  # Combined score
    
    def _get_sector_score(self, sector):
        """Get sector momentum score"""
        sector_scores = {
            'Information Technology': 0.8,
            'Financial Services': 0.6,
            'Consumer Goods': 0.7,
            'Healthcare': 0.75,
            'Energy': 0.5,
            'Automobile': 0.65,
            'Telecommunications': 0.55,
            'Real Estate': 0.6
        }
        return sector_scores.get(sector, 0.6)
    
    def train(self, stock_data, returns_data=None):
        """Train the stock scoring models"""
        if not stock_data:
            # Create synthetic training data for demo
            self._create_synthetic_training_data()
            return True
            
        features = self.prepare_features(stock_data)
        
        if returns_data is None:
            # Generate synthetic returns for training
            targets = np.random.normal(0.08, 0.15, len(features))  # 8% mean return, 15% std
        else:
            targets = returns_data
            
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features_scaled, targets, test_size=0.2, random_state=42
        )
        
        # Train models
        self.fundamental_model.fit(X_train, y_train)
        self.technical_model.fit(X_train, y_train)
        
        self.is_trained = True
        return True
    
    def _create_synthetic_training_data(self):
        """Create synthetic training data for initial model"""
        np.random.seed(42)
        n_samples = 1000
        
        features = np.random.normal(0, 1, (n_samples, 8))
        targets = np.random.normal(0.08, 0.15, n_samples)
        
        self.scaler.fit(features)
        self.fundamental_model.fit(features, targets)
        self.technical_model.fit(features, targets)
        self.is_trained = True
    
    def score_stocks(self, stock_data):
        """Score all stocks and return rankings"""
        if not self.is_trained:
            self.train([])  # Train with synthetic data
            
        features = self.prepare_features(stock_data)
        
        if len(features) == 0:
            return []
            
        features_scaled = self.scaler.transform(features)
        
        # Get predictions from both models
        fundamental_scores = self.fundamental_model.predict(features_scaled)
        technical_scores = self.technical_model.predict(features_scaled)
        
        # Combine scores
        combined_scores = (fundamental_scores + technical_scores) / 2
        
        # Create results
        results = []
        for i, stock in enumerate(stock_data):
            results.append({
                'symbol': stock.get('symbol'),
                'name': stock.get('company_name'),
                'sector': stock.get('sector'),
                'score': float(combined_scores[i]),
                'fundamental_score': float(fundamental_scores[i]),
                'technical_score': float(technical_scores[i]),
                'current_price': stock.get('current_price'),
                'market_cap': stock.get('market_cap'),
                'pe_ratio': stock.get('pe_ratio'),
                'dividend_yield': stock.get('dividend_yield')
            })
            
        # Sort by combined score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def save_model(self, filepath):
        """Save the trained model"""
        model_data = {
            'fundamental_model': self.fundamental_model,
            'technical_model': self.technical_model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath):
        """Load a pre-trained model"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.fundamental_model = model_data['fundamental_model']
            self.technical_model = model_data['technical_model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            return True
        return False
