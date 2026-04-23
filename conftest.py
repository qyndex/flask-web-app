"""Shared pytest fixtures for the Flask web app test suite."""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Category, Post, User


@pytest.fixture(scope="session")
def app():
    """Session-scoped Flask application using an in-memory SQLite database.

    The schema is created once for the whole session and torn down at the end.
    Individual tests use the ``db`` fixture to wrap each test in a savepoint
    so the database is left clean between tests without needing a full
    recreate.
    """
    flask_app = create_app("config.TestingConfig")
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Plain (unauthenticated) Flask test client — one per test."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Function-scoped database fixture.

    Wraps each test in a ``SAVEPOINT`` so that all changes are rolled back
    when the test finishes, leaving the schema intact for the next test.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind the session to this connection so it shares the transaction.
        _db.session.bind = connection  # type: ignore[attr-defined]

        yield _db

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def user(db):
    """A persisted regular User."""
    u = User(username="testuser", email="test@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.flush()
    return u


@pytest.fixture()
def admin_user(db):
    """A persisted admin User."""
    u = User(username="adminuser", email="admin@example.com", is_admin=True)
    u.set_password("adminpass123")
    db.session.add(u)
    db.session.flush()
    return u


@pytest.fixture()
def category(db):
    """A persisted Category."""
    cat = Category(name="Technology", slug="technology")
    db.session.add(cat)
    db.session.flush()
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
    db.session.flush()
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
    db.session.flush()
    return post


@pytest.fixture()
def logged_in_client(app, user, db):
    """A test client with *user* already authenticated.

    Uses ``db.session.commit()`` so the user row is visible through the
    separate connection that Flask's test client opens.
    """
    db.session.commit()
    with app.test_client() as c:
        c.post(
            "/auth/login",
            data={"username": user.username, "password": "password123"},
            follow_redirects=True,
        )
        yield c
