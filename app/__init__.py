import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

login_manager.login_view = "auth.login"


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///skillquest.db"
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth.routes import auth
    from .admin.routes import admin
    from .student.routes import student

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student)

    @app.route("/")
    def home():
        return """
        <h1>Skill Quest 2026</h1>
        <p>Educadd Online Examination System</p>
        """

    with app.app_context():
        db.create_all()

    return app
