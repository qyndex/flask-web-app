"""Authentication routes for the Flask web app."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    user = db.session.execute(
        db.select(User).where(User.username == username)
    ).scalar_one_or_none()
    if user is None or not user.check_password(password):
        flash("Invalid username or password.", "danger")
        return redirect(url_for("auth.login"))
    login_user(user, remember=bool(request.form.get("remember")))
    return redirect(request.args.get("next") or url_for("main.dashboard"))


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    username = request.form.get("username", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    if not username or not email or not password:
        flash("All fields are required.", "danger")
        return redirect(url_for("auth.register"))
    existing = db.session.execute(
        db.select(User).where(User.username == username)
    ).scalar_one_or_none()
    if existing:
        flash("Username already taken.", "danger")
        return redirect(url_for("auth.register"))
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Account created — please log in.", "success")
    return redirect(url_for("auth.login"))
