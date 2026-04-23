# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask Web App — Full Flask 3 web app with Jinja2 templates, Flask-Login authentication, SQLAlchemy 2 models, marshmallow schemas, and a REST API alongside HTML views.

Built with Flask 3.x, Python 3.13, and SQLAlchemy.

## Commands

```bash
pip install -r requirements.txt          # Install dependencies
cp .env.example .env                     # Set environment variables
flask run --reload                       # Start dev server (http://localhost:5000)
python -m pytest                         # Run all tests
python -m pytest -v --tb=short          # Verbose test run
ruff check .                             # Lint
ruff format .                            # Format
mypy .                                   # Type check
```

## Architecture

```
app/
  __init__.py      # create_app() factory
  extensions.py    # Shared extension instances (db, ma, migrate, login_manager)
  models.py        # SQLAlchemy 2 models: User, Category, Post
  schemas.py       # Marshmallow schemas for API serialisation
  main/
    routes.py      # HTML views: index, post_detail, dashboard
  auth/
    routes.py      # Auth views: login, logout, register
  api/
    routes.py      # JSON REST API: /api/posts, /api/categories
config.py          # DevelopmentConfig / TestingConfig / ProductionConfig
conftest.py        # Shared pytest fixtures (app, client, db, user, ...)
tests/
  test_views.py    # View + route tests via Flask test client
  test_models.py   # Unit tests for SQLAlchemy models
wsgi.py            # Gunicorn entry point
```

## Rules

- Use Flask Blueprints for route organisation — `main_bp`, `auth_bp`, `api_bp`
- SQLAlchemy 2 style (`db.session.execute(db.select(...))`) — no raw SQL, no legacy `Model.query`
- Environment variables for all configuration — never hardcode secrets
- Error handlers for 404, 500, and validation errors
- `config.TestingConfig` for tests — `TESTING=True`, `WTF_CSRF_ENABLED=False`, `SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"`

## Testing Conventions

- Fixtures live in `conftest.py` — do NOT name helper classes with `Test` prefix
- Use the `app` fixture (session-scoped) and `db` fixture (function-scoped with rollback) from `conftest.py`
- The `logged_in_client` fixture provides an authenticated test client
- Run a single test: `python -m pytest tests/test_views.py::TestIndexView::test_returns_200 -v`
- Coverage: `python -m pytest --cov=app --cov-report=term-missing`

## Models

| Model    | Table        | Key fields |
|----------|-------------|------------|
| User     | users       | id, username, email, password_hash, is_admin, created_at |
| Category | categories  | id, name, slug |
| Post     | posts       | id, title, slug, body, is_published, view_count, author_id, category_id, created_at, updated_at |

- `User.set_password(pw)` / `User.check_password(pw)` — Werkzeug hashing
- `Post.author` → `User` (many-to-one), `Post.category` → `Category` (optional many-to-one)
- Both `User.posts` and `Category.posts` are `lazy="dynamic"` — call `.all()` to materialise

## API Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/posts | No | List published posts |
| POST | /api/posts | Login | Create a post |
| GET | /api/posts/<id> | No | Get a post by ID |
| GET | /api/categories | No | List categories |

- POST `/api/posts` auto-generates `slug` from the title
- Schemas: `PostSchema`, `CategorySchema`, `UserSchema` in `app/schemas.py`

## Common Gotchas

1. `SQLALCHEMY_DATABASE_URI` must be set in production — the default `sqlite:///dev.db` is for development only
2. `SECRET_KEY` must be a long random string in production — never use the default
3. `WTF_CSRF_ENABLED` is `False` in `TestingConfig` to allow form POSTs in tests
4. Flask-Login `login_view = "auth.login"` — always use blueprint-qualified endpoint names
5. SQLAlchemy 2 style: `db.session.execute(db.select(Model).where(...))` — not `Model.query`
6. `dynamic` relationships (`user.posts`, `category.posts`) return a query object — use `.all()` to get a list
