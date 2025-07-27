from app import create_app, db
import os
import sys

app = create_app()

if __name__ == "__main__":
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]

    # Handle SQLite - ensure folder exists
    if db_uri.startswith("sqlite:///"):
        # Extract file path after sqlite:///
        db_path = db_uri.replace("sqlite:///", "", 1)
        db_folder = os.path.dirname(db_path)
        abs_db_path = os.path.abspath(db_path)
        abs_db_folder = os.path.abspath(db_folder)

        print("Resolved DB URI:", db_uri)
        print("Absolute DB file path:", abs_db_path)
        print("Absolute DB folder path:", abs_db_folder)

        # Create folder if needed
        if db_folder and not os.path.exists(db_folder):
            try:
                os.makedirs(db_folder, exist_ok=True)
                print(f"Created database directory: {abs_db_folder}")
            except Exception as e:
                print(f"Failed to create database folder {abs_db_folder}: {e}")
                sys.exit(1)
        elif db_folder:
            print(f"Database folder exists: {abs_db_folder}")

    # Create tables inside app context
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created (or already exist).")
        except Exception as e:
            print("Error while creating database tables:", e)
            sys.exit(1)

    # Start the Flask server
    app.run(host="0.0.0.0", port=5000, debug=True)
