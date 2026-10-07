from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from ..models import User


auth = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):

            login_user(user)

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

            return redirect(url_for("student.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth.route("/logout")
def logout():

    logout_user()

    return redirect(url_for("auth.login"))