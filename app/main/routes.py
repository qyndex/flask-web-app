"""Main HTML routes for the Flask web app."""
import re

from flask import Blueprint, abort, flash, render_template, redirect, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Category, ContactMessage, Post

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


@main_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def create_post():
    """Create a new post."""
    categories = db.session.execute(db.select(Category)).scalars().all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category_id = request.form.get("category_id") or None
        is_published = bool(request.form.get("is_published"))

        if not title or not body:
            flash("Title and content are required.", "danger")
            return render_template("main/create_post.html", categories=categories)

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        # Ensure unique slug
        existing = db.session.execute(
            db.select(Post).where(Post.slug == slug)
        ).scalar_one_or_none()
        if existing:
            slug = f"{slug}-{db.session.execute(db.select(db.func.count(Post.id))).scalar()}"

        post = Post(
            title=title,
            slug=slug,
            body=body,
            is_published=is_published,
            author_id=current_user.id,
            category_id=int(category_id) if category_id else None,
        )
        db.session.add(post)
        db.session.commit()
        flash("Post created successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("main/create_post.html", categories=categories)


@main_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    """Edit an existing post."""
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if post.author_id != current_user.id:
        abort(403)

    categories = db.session.execute(db.select(Category)).scalars().all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category_id = request.form.get("category_id") or None
        is_published = bool(request.form.get("is_published"))

        if not title or not body:
            flash("Title and content are required.", "danger")
            return render_template("main/edit_post.html", post=post, categories=categories)

        post.title = title
        post.body = body
        post.is_published = is_published
        post.category_id = int(category_id) if category_id else None
        db.session.commit()
        flash("Post updated successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("main/edit_post.html", post=post, categories=categories)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact form — persists to DB."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, subject, message]):
            flash("All fields are required.", "danger")
            return render_template("main/contact.html")

        msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent successfully. We'll get back to you soon!", "success")
        return redirect(url_for("main.contact"))

    return render_template("main/contact.html")
