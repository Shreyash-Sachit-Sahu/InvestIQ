from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(240), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist))
    updated_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist), onupdate=datetime.now(datetime.timezone.ist))
    portfolios = db.relationship("Portfolio", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False, default="Default Portfolio")
    created_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist))
    updated_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist), onupdate=datetime.now(datetime.timezone.ist))
    holdings = db.relationship("Holding", backref="portfolio", lazy=True, cascade="all, delete-orphan")

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolio.id"), nullable=False)
    symbol = db.Column(db.String(32), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_buy_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist))
    updated_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist), onupdate=datetime.now(datetime.timezone.ist))
    __table_args__ = (
        db.UniqueConstraint('portfolio_id', 'symbol', name='uniq_portfolio_symbol'),
    )
