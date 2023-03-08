import click
import hashlib
from datetime import datetime
from src.app import db
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask.cli import with_appcontext


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Thread(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    messages = db.relationship("Message", back_populates="thread", cascade="all, delete, delete-orphan")

    def serialize(self):
        return {
            "thread_id": self.id,
            "title": self.title
        }

    def deserialize(self, doc):
        self.title = doc["title"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["title"]
        }
        props = schema["properties"] = {}
        props["title"] = {
            "description": "Thread title",
            "type": "string",
            "maxLength": 200
        }
        return schema


class Message(db.Model):
    message_id = db.Column(db.Integer, unique=True, primary_key=True)
    message_content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('message.message_id', ondelete="CASCADE"))

    parent = db.relationship("Message", remote_side=[message_id])
    thread = db.relationship("Thread", back_populates="messages")
    reactions = db.relationship("Reaction", back_populates="message", cascade="all, delete")
    media = db.relationship("Media", back_populates="message", cascade="all, delete")
    user = db.relationship("User", back_populates="messages")
    
    def serialize(self):
        return {
            "message_id": self.message_id,
            "message_content": self.message_content,
            "timestamp": self.timestamp,
            "sender_id": self.sender_id,
            "thread_ID": self.thread_id,
            "parent_ID": self.parent_id
        }

    def deserialize(self, doc):
        self.message_content = doc["message_content"]
        self.timestamp = datetime.fromisoformat(doc["timestamp"])
        self.sender_id = doc["sender_id"]
        self.thread_id = doc["thread_id"]
        self.parent_id = doc.get("parent_id")

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["message_content", "timestamp",
                         "sender_id", "thread_id"]
        }
        props = schema["properties"] = {}
        props["message_content"] = {
            "description": "Message content",
            "type": "string",
            "maxLength": 500
        }
        props["timestamp"] = {
            "description": "Message timestamp",
            "type": "string",
            "format": "date-time"
        }
        props["sender_id"] = {
            "description": "Message sender identification",
            "type": "integer"
        }
        props["thread_id"] = {
            "description": "Thread identification",
            "type": "integer"
        }
        return schema


class User(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    messages = db.relationship("Message", back_populates="user", cascade="all, delete")
    reactions = db.relationship("Reaction", back_populates="user", cascade="all, delete")
    key = db.relationship("ApiKey", back_populates="user", uselist=False)

    def serialize(self):
        return {
            "user_id": self.id,
            "username": self.username
        }

    def deserialize(self, doc):
        self.username = doc["username"]
        self.password = self.password_hash(doc["password"])

    @staticmethod
    def password_hash(password):
        return hashlib.sha256(password.encode()).digest()

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["username", "password"]
        }
        props = schema["properties"] = {}
        props["username"] = {
            "description": "Unique username for the user",
            "type": "string",
            "maxLength": 16,
        }
        props["password"] = {
            "description": "Password for the user",
            "type": "string",
            "maxLength": 32
        }
        return schema


class Reaction(db.Model):
    reaction_id = db.Column(db.Integer, unique=True, primary_key=True)
    reaction_type = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    user = db.relationship("User", back_populates="reactions")
    message = db.relationship("Message", back_populates="reactions")

    def deserialize(self, doc):
        self.reaction_type = doc["reaction_type"]
        self.user_id = doc["user_id"]
        self.message_id = doc["message_id"]

    def serialize(self):
        data = {
            "reaction_id": str(self.reaction_id),
            "reaction_type": str(self.reaction_type),
            "user_id": str(self.user_id),
            "message_id": str(self.message_id)
        }
        return data

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["reaction_type", "user_id", "message_id"],
        }
        props = schema["properties"] = {}
        props["reaction_type"] = {
            "type": "integer",
        }
        props["user_id"] = {
            "type": "integer",
        }
        props["message_id"] = {
            "type": "integer",
        }
        return schema


class Media(db.Model):
    media_id = db.Column(db.Integer, primary_key=True)
    media_url = db.Column(db.String(128), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    message = db.relationship("Message", back_populates="media")

    def deserialize(self, doc):
        self.media_url = doc["media_url"]
        self.message_id = doc["message_id"]

    def serialize(self):
        data = {
            "media_id": str(self.media_id),
            "media_url": str(self.media_url),
            "message_id": str(self.message_id)
        }
        return data
    
    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["media_url", "message_id"],
        }
        props = schema["properties"] = {}
        props["media_url"] = {
            "description": "Web URL to an image file",
            "type": "string",
            "maxLength": 128,
            "format": "uri",
            # Regex to check if url ends with .png or .jpg
            "pattern": "(.png|.jpg)$"
        }
        props["message_id"] = {
            "description": "Message that the image is sent with",
            "type": "integer",
        }
        return schema


class ApiKey(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)

    user = db.relationship("User", back_populates="key")

    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()


@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()


@click.command("populate-db")
def populate_db():
    from src.utils import sample_database
    sample_database()
