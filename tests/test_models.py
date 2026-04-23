"""Tests for SQLAlchemy models: User, Category, Post."""
import pytest
from werkzeug.security import check_password_hash

from app.models import Category, Post, User


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    """Unit tests for the User model."""

    def test_create_user(self, db):
        u = User(username="alice", email="alice@example.com")
        u.set_password("secret")
        db.session.add(u)
        db.session.commit()
        assert u.id is not None

    def test_set_password_hashes_value(self, db):
        u = User(username="bob", email="bob@example.com")
        u.set_password("mypassword")
        assert u.password_hash != "mypassword"
        assert check_password_hash(u.password_hash, "mypassword")

    def test_check_password_returns_true_for_correct(self, db):
        u = User(username="carol", email="carol@example.com")
        u.set_password("correct")
        assert u.check_password("correct") is True

    def test_check_password_returns_false_for_wrong(self, db):
        u = User(username="dave", email="dave@example.com")
        u.set_password("correct")
        assert u.check_password("wrong") is False

    def test_is_admin_defaults_to_false(self, db):
        u = User(username="eve", email="eve@example.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()
        assert u.is_admin is False

    def test_username_is_unique(self, db, user):
        duplicate = User(username=user.username, email="other@example.com")
        duplicate.set_password("pass")
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_email_is_unique(self, db, user):
        duplicate = User(username="uniqueuser", email=user.email)
        duplicate.set_password("pass")
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_repr(self, user):
        assert "testuser" in repr(user)

    def test_created_at_set_on_insert(self, db):
        u = User(username="frank", email="frank@example.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()
        assert u.created_at is not None

    def test_user_mixin_is_active_by_default(self, user):
        # UserMixin.is_active returns True by default
        assert user.is_active is True

    def test_user_is_authenticated_after_creation(self, user):
        # get_id returns a string representation of the PK
        assert user.get_id() == str(user.id)


# ---------------------------------------------------------------------------
# Category model
# ---------------------------------------------------------------------------


class TestCategoryModel:
    """Unit tests for the Category model."""

    def test_create_category(self, db):
        cat = Category(name="Science", slug="science")
        db.session.add(cat)
        db.session.commit()
        assert cat.id is not None

    def test_name_is_unique(self, db, category):
        duplicate = Category(name=category.name, slug="other-slug")
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_slug_is_unique(self, db, category):
        duplicate = Category(name="Other Name", slug=category.slug)
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_repr(self, category):
        assert category.name in repr(category)


# ---------------------------------------------------------------------------
# Post model
# ---------------------------------------------------------------------------


class TestPostModel:
    """Unit tests for the Post model."""

    def test_create_post(self, db, user):
        post = Post(
            title="Test Post",
            slug="test-post",
            body="Body text",
            author_id=user.id,
        )
        db.session.add(post)
        db.session.commit()
        assert post.id is not None

    def test_is_published_defaults_to_false(self, db, user):
        post = Post(
            title="Unpublished",
            slug="unpublished",
            body="Body",
            author_id=user.id,
        )
        db.session.add(post)
        db.session.commit()
        assert post.is_published is False

    def test_view_count_defaults_to_zero(self, db, user):
        post = Post(
            title="View Count Post",
            slug="view-count-post",
            body="Body",
            author_id=user.id,
        )
        db.session.add(post)
        db.session.commit()
        assert post.view_count == 0

    def test_author_relationship(self, published_post, user):
        assert published_post.author.id == user.id
        assert published_post.author.username == user.username

    def test_category_relationship(self, published_post, category):
        assert published_post.category.id == category.id
        assert published_post.category.name == category.name

    def test_category_is_optional(self, db, user):
        post = Post(
            title="No Category Post",
            slug="no-category-post",
            body="Body",
            author_id=user.id,
            category_id=None,
        )
        db.session.add(post)
        db.session.commit()
        assert post.category is None

    def test_slug_is_unique(self, db, published_post, user):
        duplicate = Post(
            title="Different Title",
            slug=published_post.slug,
            body="Body",
            author_id=user.id,
        )
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_created_at_set_on_insert(self, published_post):
        assert published_post.created_at is not None

    def test_updated_at_set_on_insert(self, published_post):
        assert published_post.updated_at is not None

    def test_repr(self, published_post):
        assert published_post.title in repr(published_post)

    def test_user_posts_backref(self, user, published_post, db):
        # user.posts is a dynamic relationship — use .all() to materialise
        post_ids = [p.id for p in user.posts]
        assert published_post.id in post_ids

    def test_category_posts_backref(self, category, published_post, db):
        post_ids = [p.id for p in category.posts]
        assert published_post.id in post_ids
