#!/usr/bin/env python3
"""Initialize data for the application"""

import os
import sys
import json

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
            
            print("🏦 Using yfinance (Yahoo Finance) for real NSE data")
            print("📊 This will fetch comprehensive financial data including:")
            print("   • Current stock prices")
            print("   • Market capitalization")
            print("   • P/E ratios")
            print("   • Dividend yields")
            print("   • Beta values")
            print("   • Volume data")
            print("")
            
            # Initialize NSE data service
            nse_service = NSEDataService()
            
            # Test yfinance connection
            print("🔍 Testing yfinance connection...")
            test_result = nse_service.test_api_connection()
            
            if not test_result['success']:
                print(f"❌ yfinance connection test failed: {test_result['error']}")
                if 'troubleshooting' in test_result:
                    print("🛠️  Troubleshooting steps:")
                    for step in test_result['troubleshooting']:
                        print(f"   • {step}")
                print("\n⚠️  Cannot proceed without yfinance connection")
                return
            
            print("✅ yfinance connection successful!")
            print(f"📊 Test data: {test_result.get('test_data', {})}")
            print("")
            
            # Get usage stats (no limits with yfinance!)
            stats = nse_service.get_api_usage_stats()
            print(f"📈 API Provider: {stats.get('api_provider')}")
            print(f"📊 Daily Limit: {stats.get('daily_limit')}")
            print(f"⏳ Starting stock data update (5-10 minutes)...")
            print("")
            
            # Update stock data with yfinance
            nse_service.update_stock_data()
            
            # Verify results
            from app.models.stock import NSEStock
            stock_count = NSEStock.query.count()
            print("")
            print(f"📈 Database now contains {stock_count} stocks with REAL NSE data!")
            
            # Show sample data
            if stock_count > 0:
                sample_stock = NSEStock.query.first()
                print(f"📊 Sample: {sample_stock.company_name} - ₹{sample_stock.current_price}")
            
            # Create models directory
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            os.makedirs(models_dir, exist_ok=True)
            print("✅ Models directory created")
            
            print("")
            print("🚀 Application initialization complete!")
            print("💼 Your resume project now has REAL NSE financial data!")
            print("💡 Run: python run.py")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    init_data()
