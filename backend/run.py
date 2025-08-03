import os
from app import create_app, db
from flask_migrate import upgrade

# Create Flask application
app = create_app()

# Ensure models are imported for database creation
from app.models import user, portfolio, stock, recommendation

@app.before_first_request
def create_tables():
    """Create database tables before first request"""
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

if __name__ == '__main__':
    # Run database migrations
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            print("Database initialized")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
