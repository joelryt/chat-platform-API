import os
import pytest
import tempfile
from src.app import create_app, db
from src.models import Thread, Message, User, Reaction, Media, populate_db
from src.utils import sample_database
from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    app = create_app(config)

    with app.app_context():
        db.create_all()
        _populate_test_db()

    yield app.test_client()

    os.close(db_fd)
    os.unlink(db_fname)


def _populate_test_db():
    sample_database()


class TestUserItem(object):

    RESOURCE_URL = "/api/users/User1/"
    INVALID_URL = "/api/users/non-existing-user/"

    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
