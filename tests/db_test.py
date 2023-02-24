import os
import pytest
import tempfile

from datetime import datetime
from src.app import create_app, db
from src.models import Thread, Message, User, Reaction, Media
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError


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
    return Thread()


def _get_message(user=None, thread=None, parent=None):
    return Message(
        message_content="hello world",
        timestamp=datetime.now(),
        user=user,
        thread=thread,
        parent=parent
    )


def _get_user(username="username"):
    return User(
        username=username,
        password="password"
    )


def _get_reaction(user=None, message=None):
    return Reaction(
        reaction_type=1,
        user=user,
        message=message
    )


def _get_media(media_url="url", message=None):
    return Media(
        media_url=media_url,
        message=message
    )


def test_create_instances(app):
    """
    Tests creation of all database model instances.
    """
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


def test_message_relationships(app):
    """
    Tests the one-to-many relationships between a thread and messages and a user and messages,
    and the recursive relationship between two messages.
    """
    with app.app_context():
        thread = _get_thread()
        user = _get_user()
        message1 = _get_message(user=user, thread=thread)
        message2 = _get_message(user=user, thread=thread, parent=message1)
        assert message1.thread_ID == thread.id
        assert message2.thread_ID == thread.id
        assert message2.parent_ID == message1.message_id
        assert message1.sender_id == user.id
        assert message2.sender_id == user.id
        db.session.add(thread)
        db.session.add(user)
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()


def test_reaction_relationships(app):
    """
    Tests the one-to-many relationships between a message and reactions and a user and reactions.
    """
    with app.app_context():
        thread = _get_thread()
        user = _get_user()
        message = _get_message(user, thread)
        reaction1 = _get_reaction(user=user, message=message)
        reaction2 = _get_reaction(user=user, message=message)
        assert reaction1.message_id == message.message_id
        assert reaction2.message_id == message.message_id
        assert reaction1.user_id == user.id
        assert reaction2.user_id == user.id
        db.session.add(thread)
        db.session.add(user)
        db.session.add(reaction1)
        db.session.add(reaction2)
        db.session.commit()


def test_media_relationships(app):
    """
    Tests the one-to-many relationship between a message and media.
    """
    with app.app_context():
        thread = _get_thread()
        user = _get_user()
        message = _get_message(user, thread)
        media1 = _get_media(media_url="url1", message=message)
        media2 = _get_media(media_url="url2", message=message)
        assert media1.message_id == message.message_id
        assert media2.message_id == message.message_id
        db.session.add(thread)
        db.session.add(user)
        db.session.add(media1)
        db.session.add(media2)
        db.session.commit()


def test_message_columns(app):
    """
    Tests column restrictions on Message table.
    """
    with app.app_context():
        thread = _get_thread()
        user = _get_user()
        message = _get_message(user=user, thread=thread)
        message.message_content = None
        db.session.add(thread)
        db.session.add(user)
        db.session.add(message)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        message = _get_message(user=user, thread=thread)
        message.timestamp = str(datetime.now())
        db.session.add(thread)
        db.session.add(user)
        db.session.add(message)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        message.timestamp = None
        db.session.add(thread)
        db.session.add(user)
        db.session.add(message)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        message = _get_message(user=user, thread=None)
        db.session.add(message)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        message = _get_message(user=None, thread=thread)
        db.session.add(message)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_user_columns(app):
    """
    Tests column restrictions on User table.
    """
    with app.app_context():
        user = _get_user()
        user.username = None
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        user = _get_user()
        user.password = None
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        user1 = _get_user()
        user2 = _get_user()
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_reaction_columns(app):
    """
    Tests column restrictions on Reaction table.
    """
    with app.app_context():
        user = _get_user()
        thread = _get_thread()
        message = _get_message(user, thread)
        reaction = _get_reaction(user=user, message=message)
        reaction.reaction_type = None
        db.session.add(user)
        db.session.add(thread)
        db.session.add(message)
        db.session.add(reaction)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        reaction = _get_reaction(user=None, message=message)
        db.session.add(user)
        db.session.add(thread)
        db.session.add(message)
        db.session.add(reaction)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        reaction = _get_reaction(user=user, message=None)
        db.session.add(user)
        db.session.add(thread)
        db.session.add(message)
        db.session.add(reaction)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_media_columns(app):
    """
    Tests column restrictions on Media table.
    """
    with app.app_context():
        user = _get_user()
        thread = _get_thread()
        message = _get_message(user, thread)
        media1 = _get_media(message=message)
        media2 = _get_media(message=message)
        db.session.add(user)
        db.session.add(thread)
        db.session.add(message)
        db.session.add(media1)
        db.session.add(media2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        media = _get_media(message=None)
        db.session.add(user)
        db.session.add(thread)
        db.session.add(message)
        db.session.add(media)
        with pytest.raises(IntegrityError):
            db.session.commit()
