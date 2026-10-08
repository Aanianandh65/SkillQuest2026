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

    # --------------------------------------------------
    # SECRET KEY
    # --------------------------------------------------

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///skillquest.db"
    )

    # Convert old Render PostgreSQL URL format if necessary
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --------------------------------------------------
    # INITIALIZE EXTENSIONS
    # --------------------------------------------------

    db.init_app(app)
    login_manager.init_app(app)

    # --------------------------------------------------
    # MODELS
    # --------------------------------------------------

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --------------------------------------------------
    # BLUEPRINTS
    # --------------------------------------------------

    from .auth.routes import auth
    from .admin.routes import admin
    from .student.routes import student

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student)

    # --------------------------------------------------
    # HOME PAGE
    # --------------------------------------------------

    @app.route("/")
    def home():
        return """
        <h1>Skill Quest 2026</h1>
        <p>Educadd Online Examination System</p>
        """

    # --------------------------------------------------
    # DATABASE INITIALIZATION
    # --------------------------------------------------

    with app.app_context():

        # Create all required tables
        db.create_all()

        # --------------------------------------------------
        # CREATE DEFAULT ADMIN
        # --------------------------------------------------

        admin_username = os.getenv(
            "ADMIN_USERNAME",
            "Educadd_Admin"
        )

        admin_email = os.getenv(
            "ADMIN_EMAIL",
            "educaddskillquest@gmail.com"
        )

        admin_password = os.getenv(
            "ADMIN_PASSWORD",
            "Admin_educadd"
        )

        existing_admin = User.query.filter_by(
            username=admin_username
        ).first()

        if not existing_admin:

            admin = User(
                username=admin_username,
                email=admin_email,
                role="admin"
            )

            admin.set_password(admin_password)

            db.session.add(admin)
            db.session.commit()

            print("----------------------------------------")
            print("Admin account created successfully.")
            print("Username:", admin_username)
            print("----------------------------------------")

        else:

            print("----------------------------------------")
            print("Admin account already exists.")
            print("----------------------------------------")

    return app