"""Shared pytest fixtures for the Flask web app test suite."""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Category, ContactMessage, Post, User


@pytest.fixture(scope="session")
def app():
    """Session-scoped Flask application using an in-memory SQLite database."""
    flask_app = create_app("config.TestingConfig")
    yield flask_app


@pytest.fixture(autouse=True)
def db(app):
    """Function-scoped database fixture.

    Creates all tables before each test and drops them after, so every test
    starts with a clean database.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Plain (unauthenticated) Flask test client — one per test."""
    return app.test_client()


@pytest.fixture()
def user(db):
    """A persisted regular User."""
    u = User(username="testuser", email="test@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def admin_user(db):
    """A persisted admin User."""
    u = User(username="adminuser", email="admin@example.com", is_admin=True)
    u.set_password("adminpass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def category(db):
    """A persisted Category."""
    cat = Category(name="Technology", slug="technology")
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture()
def published_post(db, user, category):
    """A persisted published Post."""
    post = Post(
        title="Hello World",
        slug="hello-world",
        body="This is the body of the post.",
        is_published=True,
        author_id=user.id,
        category_id=category.id,
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture()
def draft_post(db, user):
    """A persisted unpublished Post."""
    post = Post(
        title="Draft Post",
        slug="draft-post",
        body="This post is not published yet.",
        is_published=False,
        author_id=user.id,
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture()
def logged_in_client(app, user, db):
    """A test client with *user* already authenticated."""
    with app.test_client() as c:
        c.post(
            "/auth/login",
            data={"username": user.username, "password": "password123"},
            follow_redirects=True,
        )
        yield c
