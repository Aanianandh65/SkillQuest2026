from app import create_app, db
from app.models import User


app = create_app()


with app.app_context():

    existing_admin = User.query.filter_by(
        username="admin"
    ).first()

    if existing_admin:

        print("Admin already exists.")

    else:

        admin = User(
            username="admin",
            email="admin@educadd.com",
            role="admin"
        )

        admin.set_password("Admin@123")

        db.session.add(admin)

        db.session.commit()

        print("Admin created successfully.")
        print("Username: admin")
        print("Password: Admin@123")