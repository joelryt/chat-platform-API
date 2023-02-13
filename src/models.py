from src.app import db
from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Thread(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)

    messages = db.relationship("Message", back_populates="thread")


class Message(db.Model):
    message_id = db.Column(db.Integer, unique=True, primary_key=True)
    message_content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender = db.Column(db.String(16), db.ForeignKey('user.username', ondelete="CASCADE"), unique=True, nullable=False)
    thread_ID = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete="CASCADE"), unique=True, nullable=False)
    parent_ID = db.Column(db.Integer, db.ForeignKey('message.message_id', ondelete="CASCADE"))

    parent = db.relationship("Message", remote_side=[message_id])
    thread = db.relationship("Thread", back_populates="messages")
    reactions = db.relationship("Reaction", back_populates="message")
    media = db.relationship("Media", back_populates="message")
    user = db.relationship("User", back_populates="messages")


class User(db.Model):
    username = db.Column(db.String(16), unique=True, primary_key=True)
    password = db.Column(db.String(32), nullable=False)

    messages = db.relationship("Message", back_populates="user")
    reactions = db.relationship("Reaction", back_populates="user")


class Reaction(db.Model):
    reaction_id = db.Column(db.Integer, unique=True, primary_key=True)
    reaction_type = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(16), db.ForeignKey("user.username", ondelete="CASCADE"), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    user = db.relationship("User", back_populates="reactions")
    message = db.relationship("Message", back_populates="reactions")


class Media(db.Model):
    media_url = db.Column(db.String(128), primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    message = db.relationship("Message", back_populates="media")
