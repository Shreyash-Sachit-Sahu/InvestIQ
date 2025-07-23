from app import create_app, db
import os

app = create_app()

if __name__ == "__main__":
    db_path = os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", ""))
    if db_path and not os.path.exists(db_path):
        os.makedirs(db_path)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
