#!/usr/bin/env python3
"""Initialize data for the application"""

import os
import sys
import json
from app import create_app, db
from app.services.nse_data_service import NSEDataService

def init_data():
    """Initialize application data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            print("✅ Database tables created")
            
            # Initialize NSE data service
            nse_service = NSEDataService()
            
            # Try to update stock data (will fall back to synthetic data if API fails)
            try:
                nse_service.update_stock_data()
                print("✅ Stock data initialized")
            except Exception as e:
                print(f"⚠️  Stock data update failed, will use synthetic data: {e}")
            
            # Create models directory
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            os.makedirs(models_dir, exist_ok=True)
            print("✅ Models directory created")
            
            print("🚀 Application initialization complete!")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_data()
