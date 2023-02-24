import click
import datetime
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

    messages = db.relationship("Message", back_populates="thread")


class Message(db.Model):
    message_id = db.Column(db.Integer, unique=True, primary_key=True)
    message_content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    thread_ID = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete="CASCADE"), nullable=False)
    parent_ID = db.Column(db.Integer, db.ForeignKey('message.message_id', ondelete="CASCADE"))

    parent = db.relationship("Message", remote_side=[message_id])
    thread = db.relationship("Thread", back_populates="messages")
    reactions = db.relationship("Reaction", back_populates="message")
    media = db.relationship("Media", back_populates="message")
    user = db.relationship("User", back_populates="messages")


class User(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    messages = db.relationship("Message", back_populates="user")
    reactions = db.relationship("Reaction", back_populates="user")


class Reaction(db.Model):
    reaction_id = db.Column(db.Integer, unique=True, primary_key=True)
    reaction_type = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    user = db.relationship("User", back_populates="reactions")
    message = db.relationship("Message", back_populates="reactions")


class Media(db.Model):
    media_url = db.Column(db.String(128), primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

    message = db.relationship("Message", back_populates="media")


@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()


@click.command("populate-db")
def populate_db():
    user1 = User(username="User1", password="password")
    user2 = User(username="User2", password="password")

    thread = Thread()
    message1 = Message(
        message_content="Thread opening message",
        timestamp=datetime.datetime.now(),
    )
    message1.user = user1
    message1.thread = thread
    media1 = Media(media_url="media1/url/")
    media1.message = message1
    reaction1 = Reaction(reaction_type=1)
    reaction1.user = user2
    reaction1.message = message1

    message2 = Message(
        message_content="Reply 1",
        timestamp=datetime.datetime.now(),
    )
    message2.user = user2
    message2.thread = thread
    message2.parent = message1
    reaction2 = Reaction(reaction_type=2)
    reaction2.user = user1
    reaction2.message = message2

    message3 = Message(
        message_content="Reply 2",
        timestamp=datetime.datetime.now(),
    )
    message3.user = user1
    message3.thread = thread
    message3.parent = message2
    media2 = Media(media_url="media2/url/")
    media2.message = message3

    db.session.add(user1)
    db.session.add(user2)
    db.session.add(thread)
    db.session.add(message1)
    db.session.add(media1)
    db.session.add(reaction1)
    db.session.add(message2)
    db.session.add(reaction2)
    db.session.add(message3)
    db.session.add(media2)
    db.session.commit()
