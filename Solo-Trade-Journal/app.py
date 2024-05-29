from flask import Flask
from views import views
from flask_sqlalchemy import SQLAlchemy
from models import db
from dotenv import load_dotenv
import os



#   Flask Configuration ( initialising the application context )
app = Flask(__name__)
app.register_blueprint(views)

#   Database Configuration
app.config['SECRET_KEY'] = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)