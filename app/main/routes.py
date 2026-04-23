"""Main HTML routes for the Flask web app."""
from flask import Blueprint, abort, render_template, redirect, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Category, Post

main_bp = Blueprint("main", __name__, template_folder="../templates")


@main_bp.get("/")
def index():
    """Homepage — recent published posts."""
    posts = (
        db.session.execute(
            db.select(Post)
            .where(Post.is_published == True)  # noqa: E712
            .order_by(Post.created_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template("main/index.html", posts=posts, categories=categories)


@main_bp.get("/posts/<slug>")
def post_detail(slug: str):
    """Single post page."""
    post = db.session.execute(
        db.select(Post).where(Post.slug == slug, Post.is_published == True)  # noqa: E712
    ).scalar_one_or_none()
    if post is None:
        abort(404)
    db.session.execute(
        db.update(Post).where(Post.id == post.id).values(view_count=Post.view_count + 1)
    )
    db.session.commit()
    return render_template("main/post_detail.html", post=post)


@main_bp.get("/dashboard")
@login_required
def dashboard():
    """Author dashboard — their posts."""
    posts = (
        db.session.execute(
            db.select(Post)
            .where(Post.author_id == current_user.id)
            .order_by(Post.created_at.desc())
        )
        .scalars()
        .all()
    )
    return render_template("main/dashboard.html", posts=posts)
