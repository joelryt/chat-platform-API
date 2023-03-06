import os
import tempfile
import pytest

from src.utils import sample_database
from src.app import create_app, db
from src.models import Thread, Message, User, Reaction, Media


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


def test_sample_database(app):
    """
    Tests creation of the sample database.
    """
    with app.app_context():
        sample_database()
        assert Thread.query.count() == 1
        assert Message.query.count() == 4
        assert User.query.count() == 3
        assert Reaction.query.count() == 3
        assert Media.query.count() == 3
