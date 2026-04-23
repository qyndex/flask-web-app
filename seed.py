"""Seed script — populates the database with sample users, categories, and posts.

Usage:
    python seed.py              # Uses DevelopmentConfig (sqlite:///dev.db)
    FLASK_CONFIG=config.TestingConfig python seed.py
"""
from __future__ import annotations

import os
import sys

from app import create_app
from app.extensions import db
from app.models import Category, ContactMessage, Post, User


USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "is_admin": True,
    },
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "alice123",
        "full_name": "Alice Johnson",
        "is_admin": False,
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "bob12345",
        "full_name": "Bob Smith",
        "is_admin": False,
    },
]

CATEGORIES = [
    {"name": "Technology", "slug": "technology"},
    {"name": "Science", "slug": "science"},
    {"name": "Travel", "slug": "travel"},
    {"name": "Lifestyle", "slug": "lifestyle"},
]

POSTS = [
    {
        "title": "Getting Started with Flask 3",
        "slug": "getting-started-with-flask-3",
        "body": (
            "Flask 3 brings exciting improvements to Python web development. "
            "The new async support, improved type hints, and streamlined API "
            "make it easier than ever to build robust web applications.\n\n"
            "In this post, we explore the key features and how to migrate "
            "your existing Flask 2 applications to take advantage of them."
        ),
        "is_published": True,
        "author": "admin",
        "category": "Technology",
    },
    {
        "title": "Understanding SQLAlchemy 2.0 Patterns",
        "slug": "understanding-sqlalchemy-2-patterns",
        "body": (
            "SQLAlchemy 2.0 introduced a new query interface that's more "
            "explicit and Pythonic. The shift from Model.query to "
            "db.session.execute(db.select(Model)) provides better type "
            "safety and more predictable behavior.\n\n"
            "We'll walk through common patterns: filtering, joining, "
            "eager loading, and pagination."
        ),
        "is_published": True,
        "author": "alice",
        "category": "Technology",
    },
    {
        "title": "The Future of Quantum Computing",
        "slug": "the-future-of-quantum-computing",
        "body": (
            "Quantum computing is rapidly advancing from laboratory "
            "experiments to practical applications. Recent breakthroughs "
            "in error correction and qubit stability are bringing us "
            "closer to quantum advantage in real-world problems.\n\n"
            "This article surveys the current state of the field and "
            "what we can expect in the next five years."
        ),
        "is_published": True,
        "author": "bob",
        "category": "Science",
    },
    {
        "title": "Hidden Gems of Southeast Asia",
        "slug": "hidden-gems-of-southeast-asia",
        "body": (
            "Beyond the popular tourist destinations lie countless "
            "hidden gems waiting to be discovered. From the limestone "
            "karsts of Phang Nga Bay to the ancient temples of Bagan, "
            "Southeast Asia offers experiences for every type of traveler.\n\n"
            "Here are ten off-the-beaten-path destinations that will "
            "make your next trip unforgettable."
        ),
        "is_published": True,
        "author": "alice",
        "category": "Travel",
    },
    {
        "title": "Draft: Upcoming Features Roadmap",
        "slug": "draft-upcoming-features-roadmap",
        "body": (
            "This is a draft post outlining our planned features for Q3. "
            "We're working on user profiles, comment threads, and an "
            "improved editor with markdown support."
        ),
        "is_published": False,
        "author": "admin",
        "category": "Technology",
    },
    {
        "title": "Building Healthy Habits with Technology",
        "slug": "building-healthy-habits-with-technology",
        "body": (
            "Technology doesn't have to be a distraction. When used "
            "intentionally, apps and devices can help us build and "
            "maintain healthy habits. From meditation apps to fitness "
            "trackers, the right tools can support your wellness journey.\n\n"
            "Here are our top recommendations for 2026."
        ),
        "is_published": True,
        "author": "bob",
        "category": "Lifestyle",
    },
]

CONTACT_MESSAGES = [
    {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "subject": "Great blog!",
        "message": "I really enjoy reading the posts on your site. Keep up the great work!",
    },
    {
        "name": "John Smith",
        "email": "john@example.com",
        "subject": "Partnership inquiry",
        "message": "We'd love to discuss a potential collaboration. Please reach out at your convenience.",
    },
]


def seed() -> None:
    """Insert seed data into the database."""
    config = os.environ.get("FLASK_CONFIG", "config.DevelopmentConfig")
    app = create_app(config)

    with app.app_context():
        # Create tables if they don't exist (for SQLite dev usage)
        db.create_all()

        # Skip if data already exists
        if db.session.execute(db.select(User)).scalar_one_or_none() is not None:
            print("Database already has data — skipping seed.")
            return

        # Users
        user_map: dict[str, User] = {}
        for data in USERS:
            user = User(
                username=data["username"],
                email=data["email"],
                full_name=data["full_name"],
                is_admin=data["is_admin"],
            )
            user.set_password(data["password"])
            db.session.add(user)
            user_map[data["username"]] = user

        db.session.flush()
        print(f"  Created {len(user_map)} users")

        # Categories
        cat_map: dict[str, Category] = {}
        for data in CATEGORIES:
            cat = Category(name=data["name"], slug=data["slug"])
            db.session.add(cat)
            cat_map[data["name"]] = cat

        db.session.flush()
        print(f"  Created {len(cat_map)} categories")

        # Posts
        for data in POSTS:
            post = Post(
                title=data["title"],
                slug=data["slug"],
                body=data["body"],
                is_published=data["is_published"],
                author_id=user_map[data["author"]].id,
                category_id=cat_map[data["category"]].id,
            )
            db.session.add(post)

        db.session.flush()
        print(f"  Created {len(POSTS)} posts")

        # Contact messages
        for data in CONTACT_MESSAGES:
            msg = ContactMessage(**data)
            db.session.add(msg)

        db.session.flush()
        print(f"  Created {len(CONTACT_MESSAGES)} contact messages")

        db.session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    seed()
