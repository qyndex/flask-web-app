# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask Web App — Full Flask 3 web app with Jinja2 templates, Flask-Login authentication, Flask-WTF CSRF protection, SQLAlchemy 2 models, Alembic migrations, marshmallow schemas, and a REST API alongside HTML views.

Built with Flask 3.x, Python 3.13, and SQLAlchemy.

## Commands

```bash
pip install -r requirements.txt          # Install dependencies
cp .env.example .env                     # Set environment variables
flask db upgrade                         # Run Alembic migrations
python seed.py                           # Seed sample data (3 users, 4 categories, 6 posts)
flask run --reload                       # Start dev server (http://localhost:5000)
python -m pytest                         # Run all tests (84 tests)
python -m pytest -v --tb=short          # Verbose test run
python -m pytest --cov=app --cov-report=term-missing  # With coverage
ruff check .                             # Lint
ruff format .                            # Format
mypy .                                   # Type check
docker compose up                        # Full stack with PostgreSQL
```

## Architecture

```
app/
  __init__.py      # create_app() factory, error handlers (404/500)
  extensions.py    # Shared extension instances (db, ma, migrate, csrf, login_manager)
  models.py        # SQLAlchemy 2 models: User, Category, Post, ContactMessage
  schemas.py       # Marshmallow schemas for API serialisation
  main/
    routes.py      # HTML views: index, post_detail, dashboard, create_post, edit_post, contact
  auth/
    routes.py      # Auth views: login, logout, register
  api/
    routes.py      # JSON REST API: /api/posts, /api/categories (CSRF-exempt)
  templates/
    base.html      # Base layout with navbar, flash messages, footer
    main/          # index, post_detail, dashboard, create_post, edit_post, contact
    auth/          # login, register
    errors/        # 404, 500
  static/
    css/style.css  # Minimal production CSS (custom properties, responsive)
config.py          # DevelopmentConfig / TestingConfig / ProductionConfig
conftest.py        # Shared pytest fixtures (app, client, db, user, ...)
seed.py            # Database seeder with sample content
migrations/        # Alembic migrations (Flask-Migrate)
  versions/
    001_initial_schema.py  # users, categories, posts, contact_messages
tests/
  test_views.py    # View + route tests via Flask test client
  test_models.py   # Unit tests for SQLAlchemy models
wsgi.py            # Gunicorn entry point
```

## Rules

- Use Flask Blueprints for route organisation — `main_bp`, `auth_bp`, `api_bp`
- SQLAlchemy 2 style (`db.session.execute(db.select(...))`) — no raw SQL, no legacy `Model.query`
- Environment variables for all configuration — never hardcode secrets
- CSRF protection via Flask-WTF — all HTML forms include `csrf_token()`, API blueprint is exempt
- Error handlers for 404, 500, and validation errors
- `config.TestingConfig` for tests — `TESTING=True`, `WTF_CSRF_ENABLED=False`, `SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"`
- All form POST routes validate required fields and flash errors on failure
- `@login_required` on all protected routes (dashboard, create/edit post)

## Testing Conventions

- Fixtures live in `conftest.py` — do NOT name helper classes with `Test` prefix
- `db` fixture is function-scoped (autouse) — creates/drops all tables per test for clean isolation
- The `logged_in_client` fixture provides an authenticated test client
- Run a single test: `python -m pytest tests/test_views.py::TestIndexView::test_returns_200 -v`
- Coverage: `python -m pytest --cov=app --cov-report=term-missing`

## Models

| Model          | Table             | Key fields |
|----------------|-------------------|------------|
| User           | users             | id, username, email, password_hash, full_name, is_admin, created_at |
| Category       | categories        | id, name, slug |
| Post           | posts             | id, title, slug, body, is_published, view_count, author_id, category_id, created_at, updated_at |
| ContactMessage | contact_messages  | id, name, email, subject, message, is_read, created_at |

- `User.set_password(pw)` / `User.check_password(pw)` — Werkzeug hashing
- `Post.author` -> `User` (many-to-one), `Post.category` -> `Category` (optional many-to-one)
- Both `User.posts` and `Category.posts` are `lazy="dynamic"` — call `.all()` to materialise

## HTML Routes

| Method | Path                  | Auth    | Description |
|--------|-----------------------|---------|-------------|
| GET    | /                     | No      | Homepage — recent published posts |
| GET    | /posts/<slug>         | No      | Single post page (increments view count) |
| GET    | /dashboard            | Login   | Author dashboard — list own posts |
| GET/POST | /posts/new          | Login   | Create a new post |
| GET/POST | /posts/<id>/edit    | Login   | Edit own post |
| GET/POST | /contact            | No      | Contact form (persists to DB) |
| GET    | /auth/login           | No      | Login page |
| POST   | /auth/login           | No      | Login action |
| GET    | /auth/register        | No      | Registration page |
| POST   | /auth/register        | No      | Registration action |
| GET    | /auth/logout          | Login   | Logout |

## API Routes

| Method | Path              | Auth  | Description |
|--------|-------------------|-------|-------------|
| GET    | /api/posts        | No    | List published posts |
| POST   | /api/posts        | Login | Create a post |
| GET    | /api/posts/<id>   | No    | Get a post by ID |
| GET    | /api/categories   | No    | List categories |

- POST `/api/posts` auto-generates `slug` from the title
- API blueprint is CSRF-exempt (for JSON clients)
- Schemas: `PostSchema`, `CategorySchema`, `UserSchema` in `app/schemas.py`

## Seed Data

Run `python seed.py` to create sample data:
- **Users**: admin/admin123 (admin), alice/alice123, bob/bob12345
- **Categories**: Technology, Science, Travel, Lifestyle
- **Posts**: 5 published + 1 draft across users and categories
- **Contact Messages**: 2 sample submissions

## Migrations

Uses Flask-Migrate (Alembic). Migrations live in `migrations/versions/`.

```bash
flask db upgrade              # Apply all pending migrations
flask db migrate -m "msg"     # Auto-generate a new migration
flask db downgrade            # Revert last migration
```

## Common Gotchas

1. `SQLALCHEMY_DATABASE_URI` must be set in production — the default `sqlite:///dev.db` is for development only
2. `SECRET_KEY` must be a long random string in production — never use the default
3. `WTF_CSRF_ENABLED` is `False` in `TestingConfig` to allow form POSTs in tests
4. Flask-Login `login_view = "auth.login"` — always use blueprint-qualified endpoint names
5. SQLAlchemy 2 style: `db.session.execute(db.select(Model).where(...))` — not `Model.query`
6. `dynamic` relationships (`user.posts`, `category.posts`) return a query object — use `.all()` to get a list
7. API blueprint is CSRF-exempt — HTML form routes are not; always include `csrf_token()` in form templates
8. The `db` test fixture drops/recreates all tables per test — no savepoint isolation (SQLite limitation)
9. `docker compose up` runs `flask db upgrade` before starting gunicorn
