"""Tests for HTML views: main blueprint, auth blueprint."""
import pytest


# ---------------------------------------------------------------------------
# Main blueprint — public pages
# ---------------------------------------------------------------------------


class TestIndexView:
    """GET / — homepage listing published posts."""

    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_shows_published_post(self, client, published_post):
        response = client.get("/")
        assert published_post.title.encode() in response.data

    def test_hides_draft_post(self, client, draft_post):
        response = client.get("/")
        assert draft_post.title.encode() not in response.data

    def test_shows_categories(self, client, category):
        response = client.get("/")
        assert category.name.encode() in response.data


class TestPostDetailView:
    """GET /posts/<slug> — single post page."""

    def test_returns_200_for_published_post(self, client, published_post):
        response = client.get(f"/posts/{published_post.slug}")
        assert response.status_code == 200

    def test_returns_404_for_unknown_slug(self, client):
        response = client.get("/posts/does-not-exist")
        assert response.status_code == 404

    def test_returns_404_for_draft_post(self, client, draft_post):
        response = client.get(f"/posts/{draft_post.slug}")
        assert response.status_code == 404

    def test_increments_view_count(self, client, published_post, db):
        initial_count = published_post.view_count
        client.get(f"/posts/{published_post.slug}")
        db.session.refresh(published_post)
        assert published_post.view_count == initial_count + 1

    def test_renders_post_body(self, client, published_post):
        response = client.get(f"/posts/{published_post.slug}")
        assert published_post.body.encode() in response.data


class TestDashboardView:
    """GET /dashboard — author dashboard, login required."""

    def test_redirects_unauthenticated_user(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_returns_200_for_logged_in_user(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        assert response.status_code == 200

    def test_shows_authors_own_posts(self, logged_in_client, published_post):
        response = logged_in_client.get("/dashboard")
        assert published_post.title.encode() in response.data


# ---------------------------------------------------------------------------
# Auth blueprint
# ---------------------------------------------------------------------------


class TestLoginView:
    """GET /auth/login and POST /auth/login."""

    def test_login_page_returns_200(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_successful_login_redirects(self, client, user):
        response = client.post(
            "/auth/login",
            data={"username": user.username, "password": "password123"},
        )
        assert response.status_code == 302

    def test_successful_login_redirects_to_dashboard(self, client, user):
        response = client.post(
            "/auth/login",
            data={"username": user.username, "password": "password123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"dashboard" in response.request.path.lower().encode() or b"dashboard" in response.data.lower()

    def test_invalid_password_stays_on_login(self, client, user):
        response = client.post(
            "/auth/login",
            data={"username": user.username, "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_unknown_user_shows_error(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "nobody", "password": "nopass"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in response.data

    def test_authenticated_user_redirected_away_from_login(self, logged_in_client):
        response = logged_in_client.get("/auth/login")
        assert response.status_code == 302


class TestLogoutView:
    """GET /auth/logout."""

    def test_logout_requires_login(self, client):
        response = client.get("/auth/logout")
        assert response.status_code == 302

    def test_logout_redirects_and_shows_flash(self, logged_in_client):
        response = logged_in_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out" in response.data


class TestRegisterView:
    """GET /auth/register and POST /auth/register."""

    def test_register_page_returns_200(self, client):
        response = client.get("/auth/register")
        assert response.status_code == 200

    def test_successful_registration_redirects_to_login(self, client):
        response = client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Account created" in response.data or b"log in" in response.data

    def test_duplicate_username_shows_error(self, client, user):
        response = client.post(
            "/auth/register",
            data={
                "username": user.username,
                "email": "other@example.com",
                "password": "pass",
            },
            follow_redirects=True,
        )
        assert b"Username already taken" in response.data

    def test_missing_fields_shows_error(self, client):
        response = client.post(
            "/auth/register",
            data={"username": "", "email": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in response.data

    def test_authenticated_user_redirected_away_from_register(self, logged_in_client):
        response = logged_in_client.get("/auth/register")
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# API blueprint — JSON endpoints
# ---------------------------------------------------------------------------


class TestApiListPosts:
    """GET /api/posts."""

    def test_returns_200(self, client):
        response = client.get("/api/posts")
        assert response.status_code == 200

    def test_returns_json(self, client):
        response = client.get("/api/posts")
        assert response.content_type == "application/json"

    def test_returns_list(self, client):
        data = client.get("/api/posts").get_json()
        assert isinstance(data, list)

    def test_includes_published_post(self, client, published_post):
        data = client.get("/api/posts").get_json()
        slugs = [p["slug"] for p in data]
        assert published_post.slug in slugs

    def test_excludes_draft_post(self, client, draft_post):
        data = client.get("/api/posts").get_json()
        slugs = [p["slug"] for p in data]
        assert draft_post.slug not in slugs


class TestApiGetPost:
    """GET /api/posts/<id>."""

    def test_returns_200_for_existing_post(self, client, published_post):
        response = client.get(f"/api/posts/{published_post.id}")
        assert response.status_code == 200

    def test_returns_post_json(self, client, published_post):
        data = client.get(f"/api/posts/{published_post.id}").get_json()
        assert data["id"] == published_post.id
        assert data["title"] == published_post.title

    def test_returns_404_for_missing_post(self, client):
        response = client.get("/api/posts/999999")
        assert response.status_code == 404


class TestApiCreatePost:
    """POST /api/posts — requires login."""

    def test_unauthenticated_request_returns_401_or_redirect(self, client):
        response = client.post(
            "/api/posts",
            json={"title": "New Post", "body": "Content here"},
        )
        assert response.status_code in (302, 401)

    def test_authenticated_user_can_create_post(self, logged_in_client):
        response = logged_in_client.post(
            "/api/posts",
            json={"title": "New API Post", "body": "Body content"},
        )
        assert response.status_code == 201

    def test_created_post_returned_as_json(self, logged_in_client):
        response = logged_in_client.post(
            "/api/posts",
            json={"title": "Another Post", "body": "Some body"},
        )
        data = response.get_json()
        assert data["title"] == "Another Post"
        assert "id" in data
        assert "slug" in data

    def test_slug_generated_from_title(self, logged_in_client):
        response = logged_in_client.post(
            "/api/posts",
            json={"title": "My Great Post Title", "body": "Body"},
        )
        data = response.get_json()
        assert data["slug"] == "my-great-post-title"


class TestApiListCategories:
    """GET /api/categories."""

    def test_returns_200(self, client):
        response = client.get("/api/categories")
        assert response.status_code == 200

    def test_returns_json_list(self, client):
        data = client.get("/api/categories").get_json()
        assert isinstance(data, list)

    def test_includes_created_category(self, client, category):
        data = client.get("/api/categories").get_json()
        names = [c["name"] for c in data]
        assert category.name in names
