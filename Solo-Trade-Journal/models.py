from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)

class TradingAccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    account_login = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    broker = db.Column(db.String, nullable=False)
    broker_server = db.Column(db.String, nullable=False)
    mt_version = db.Column(db.Integer, nullable=False)
    user = db.relationship('Users', backref=db.backref('trading_accounts', lazy=True))

class CopyTrading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    master_account = db.Column(db.String, nullable=False)
    user = db.relationship('Users', backref=db.backref('copy_trading', lazy=True))