import os
from app import create_app, db

# Create Flask application
app = create_app()

# Ensure models are imported for database creation
from app.models import user, portfolio, stock, recommendation

def init_db():
    """Create database tables if they do not exist"""
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")

if __name__ == '__main__':
    # Initialize DB at startup
    init_db()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
