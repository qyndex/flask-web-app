"""REST API routes for the Flask web app."""
from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Category, Post
from ..schemas import (
    categories_schema,
    category_schema,
    post_schema,
    posts_schema,
)

api_bp = Blueprint("api", __name__)


@api_bp.get("/posts")
def list_posts():
    posts = (
        db.session.execute(
            db.select(Post).where(Post.is_published == True).order_by(Post.created_at.desc())  # noqa: E712
        )
        .scalars()
        .all()
    )
    return jsonify(posts_schema.dump(posts))


@api_bp.post("/posts")
@login_required
def create_post():
    import re
    payload = post_schema.load(request.get_json(force=True))
    slug = re.sub(r"[^a-z0-9]+", "-", payload["title"].lower()).strip("-")
    post = Post(author_id=current_user.id, slug=slug, **payload)
    db.session.add(post)
    db.session.commit()
    return jsonify(post_schema.dump(post)), 201


@api_bp.get("/posts/<int:post_id>")
def get_post(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    return jsonify(post_schema.dump(post))


@api_bp.get("/categories")
def list_categories():
    cats = db.session.execute(db.select(Category)).scalars().all()
    return jsonify(categories_schema.dump(cats))
