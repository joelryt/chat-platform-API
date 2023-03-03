import os
import pytest
import tempfile
from sqlalchemy.engine import Engine
from sqlalchemy import event

from src.app import create_app, db
from src.utils import sample_database


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


def _get_user(username="username", password="password"):
    return {"username": username, "password": password}


def _login(client, username="user1", password="password"):
    resp = client.post(
        "/api/login/",
        json={"username": username, "password": password}
    )
    return resp

class TestUserCollection(object):

    RESOURCE_URL = "/api/users/"

    def test_post(self, client):
        """
        Tests posting to user collection.
        Case 1: Valid user posted -> 201
        Case 2: User with duplicate username posted -> 409
        Case 3: Non-json data posted -> 400/415
        Case 4: Invalid user posted -> 400
        """
        user = _get_user()
        # Case 1
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + user["username"] + "/")
        # Check that user exists after posting it
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # Case 2
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 409

        # Case 3
        resp = client.post(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_user = _get_user(password=None)
        resp = client.post(self.RESOURCE_URL, json=invalid_user)
        assert resp.status_code == 400


class TestUserItem(object):

    RESOURCE_URL = "/api/users/user1/"
    INVALID_URL = "/api/users/non-existing-user/"

    def test_get(self, client):
        """
        Tests get method for user item.
        Case 1: Get existing user -> 200
        Case 2: Get non-existing user -> 404
        """
        # Case 1
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert resp.headers["Username"] == self.RESOURCE_URL.split("/")[-2]

        # Case 2
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """
        Tests put method for user item.
        Case 1: Put valid user -> 204
        Case 2: Change existing user's password -> 204
        Case 3: Put non-json data -> 400/415
        Case 4: Put invalid user -> 400
        Case 5: Put to non-existing resource -> 404
        """
        user = _get_user(username="user1")
        # Case 1
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 204

        # Case 2
        user["password"] = "new password"
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 204

        # Case 3
        resp = client.put(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_user = _get_user(username=None)
        resp = client.put(self.RESOURCE_URL, json=invalid_user)
        assert resp.status_code == 400

        # Case 5
        resp = client.put(self.INVALID_URL, json=user)
        assert resp.status_code == 404

    def test_delete(self, client):
        """
        Tests delete method for user item.
        Case 1: Delete existing user -> 204
        Case 2: Delete previously deleted user -> 404
        Case 3: Delete non-existing resource -> 404
        """
        # Case 1
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        # Case 2
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404

        # Case 3
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestUserLogin(object):

    RESOURCE_URL = "/api/login/"

    def test_post(self, client):
        """
        Tests the login interface.
        Case 1: Login with correct credentials, create new API key -> 201
        Case 3: Login with non-existing username -> 404
        Case 4: Login with incorrect password -> 401
        Case 5: Post non-json data -> 400/415
        Case 6: Post invalid data -> 400
        """
        # Case 1
        json = _get_user("user1", "password")
        resp = client.post(self.RESOURCE_URL, json=json)
        assert resp.status_code == 201
        assert resp.headers["Api-key"] is not None

        # Case 3
        json = _get_user()
        resp = client.post(self.RESOURCE_URL, json=json)
        assert resp.status_code == 404

        # Case 3
        json = _get_user("user1", "wrong password")
        resp = client.post(self.RESOURCE_URL, json=json)
        assert resp.status_code == 401

        # Case 4
        resp = client.post(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 5
        json = _get_user(username=None)
        resp = client.post(self.RESOURCE_URL, json=json)
        assert resp.status_code == 400


class TestUserLogout(object):

    RESOURCE_URL = "/api/users/user1/logout/"
    INVALID_URL = "/api/users/non-existing-user/logout/"

    def test_post(self, client):
        """
        Tests the logout interface.
        Case 1: Logout with logged-in user -> 200
        Case 2: Logout user with no API key -> 404
        Case 3: Logout non-existing user -> 404
        """
        # Case 1
        _login(client)
        resp = client.post(self.RESOURCE_URL)
        assert resp.status_code == 200

        # Case 2
        resp = client.post(self.RESOURCE_URL)
        assert resp.status_code == 404

        # Case 3
        resp = client.post(self.INVALID_URL)
        assert resp.status_code == 404
