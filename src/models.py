import click
import hashlib
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


class Message(db.Model):
    message_id = db.Column(db.Integer, unique=True, primary_key=True)
    message_content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    thread_ID = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete="CASCADE"), nullable=False)
    parent_ID = db.Column(db.Integer, db.ForeignKey('message.message_id', ondelete="CASCADE"))

    parent = db.relationship("Message", remote_side=[message_id])
    thread = db.relationship("Thread", back_populates="messages")
    reactions = db.relationship("Reaction", back_populates="message", cascade="all, delete")
    media = db.relationship("Media", back_populates="message", cascade="all, delete")
    user = db.relationship("User", back_populates="messages")


class User(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    messages = db.relationship("Message", back_populates="user", cascade="all, delete")
    reactions = db.relationship("Reaction", back_populates="user", cascade="all, delete")
    key = db.relationship("ApiKey", back_populates="user", uselist=False)

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
            "type": "string"
        }
        props["password"] = {
            "description": "Password for the user",
            "type": "string"
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
    media_url = db.Column(db.String(128), primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    message = db.relationship("Message", back_populates="media")


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
