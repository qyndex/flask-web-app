"""Marshmallow schemas for the Flask web app API."""
from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """User serialisation schema (safe — no password fields)."""

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    is_admin = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class CategorySchema(Schema):
    """Category serialisation schema."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    slug = fields.Str(dump_only=True)


class PostSchema(Schema):
    """Post serialisation schema."""

    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    slug = fields.Str(dump_only=True)
    body = fields.Str(required=True)
    is_published = fields.Bool(load_default=False)
    view_count = fields.Int(dump_only=True)
    author = fields.Nested(UserSchema, dump_only=True)
    category = fields.Nested(CategorySchema, dump_only=True)
    category_id = fields.Int(load_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


user_schema = UserSchema()
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
