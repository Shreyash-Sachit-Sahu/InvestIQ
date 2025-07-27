from app import create_app, db
import sys

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created (or already exist).")
        except Exception as e:
            print(f"Error while creating database tables: {e}")
            sys.exit(1)

    app.run(host="0.0.0.0", port=5000, debug=False)
