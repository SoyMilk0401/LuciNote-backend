from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import Enum
from . import db

material_type_enum = Enum('pdf', 'txt', 'image', 'url', name='material_type_enum')
summary_format_enum = Enum('txt', 'pdf', 'docx', name='summary_format_enum')
item_type_enum = Enum('material', 'summary', name='item_type_enum')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_login_at = db.Column(db.TIMESTAMP, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    providers = db.relationship('UserProvider', backref='user', lazy=True, cascade="all, delete-orphan")
    materials = db.relationship('Material', backref='user', lazy=True, cascade="all, delete-orphan")
    summaries = db.relationship('Summary', backref='user', lazy=True, cascade="all, delete-orphan")
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True, cascade="all, delete-orphan")

class UserProvider(db.Model):
    __tablename__ = 'user_providers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    connected_at = db.Column(db.TIMESTAMP, server_default=func.now())

    __table_args__ = (db.UniqueConstraint('provider', 'provider_user_id'),)


class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    material_type = db.Column(material_type_enum, nullable=False)
    source_file_path = db.Column(db.String(500), nullable=True)
    original_url = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Summary(db.Model):
    __tablename__ = 'summaries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    summary_title = db.Column(db.String(255), nullable=True)
    summary_text = db.Column(db.Text, nullable=True)
    result_file_path = db.Column(db.String(500), nullable=True)
    format = db.Column(summary_format_enum, default='pdf')
    language = db.Column(db.String(10), default='ko')
    generated_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_deleted = db.Column(db.Boolean, default=False)


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_deleted = db.Column(db.Boolean, default=False)
    
    items = db.relationship('BookmarkItem', backref='bookmark', lazy=True, cascade="all, delete-orphan")


class BookmarkItem(db.Model):
    __tablename__ = 'bookmark_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookmark_id = db.Column(db.Integer, db.ForeignKey('bookmarks.id'), nullable=False)
    item_type = db.Column(item_type_enum, nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.TIMESTAMP, server_default=func.now())