import os
import pytest
import tempfile

from datetime import datetime
from src.app import create_app, db
from src.models import Thread, Message, User, Reaction, Media
from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    app = create_app(config)

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_fname)


def _get_thread():
    return Thread(
        id=0
    )


def _get_message():
    return Message(
        message_id=0,
        message_content="hello world",
        timestamp=datetime.now(),
        sender="hauki"
    )


def _get_user():
    return User(
        username="username",
        password="password"
    )


def _get_reaction():
    return Reaction(
        reaction_type=1
    )


def _get_media():
    return Media(
        media_url="url"
    )


def test_create_instances(app):
    with app.app_context():
        thread = _get_thread()
        message = _get_message()
        user = _get_user()
        reaction = _get_reaction()
        media = _get_media()

        message.thread = thread
        message.user = user
        reaction.user = user
        reaction.message = message
        media.message = message

        db.session.add(thread)
        db.session.add(message)
        db.session.add(user)
        db.session.add(reaction)
        db.session.add(media)
        db.session.commit()
        assert Thread.query.count() == 1
        assert Message.query.count() == 1
        assert User.query.count() == 1
        assert Reaction.query.count() == 1
