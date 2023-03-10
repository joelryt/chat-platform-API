import os
import re
import pytest
import tempfile
import pytz
from datetime import datetime
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
    config = {"SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname, "TESTING": True}
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


def _get_reaction(reaction_type=1, user_id=1, message_id=1):
    return {
        "reaction_type": reaction_type,
        "user_id": user_id,
        "message_id": message_id,
    }


def _get_thread(title="Thread title"):
    return {"title": title}


def _get_message(
    message_content="message content",
    timestamp=datetime.now(pytz.utc).isoformat(),
    sender_id=1,
    thread_id=1,
    parent_id=None,
):
    return {
        "message_content": message_content,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "thread_id": thread_id,
        "parent_id": parent_id,
    }


def _get_media(media_url=None, message_id=None):
    return {"media_url": media_url, "message_id": message_id}


def _login(client, username="user1", password="password"):
    """
    Helper function to log in as a user.
    Returns the created API key for the logged-in user that can be used in
    testing requests that require authentication.
    """
    resp = client.post("/api/login/", json={"username": username, "password": password})
    return resp.headers["Api-key"]


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
        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL + user["username"] + "/"
        )
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
        assert resp.headers["username"] == self.RESOURCE_URL.split("/")[-2]

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
        key = _login(client)
        user = _get_user(username="user1")
        # Case 1
        resp = client.put(self.RESOURCE_URL, headers={"Api-key": key}, json=user)
        assert resp.status_code == 204

        # Case 2
        user["password"] = "new password"
        resp = client.put(self.RESOURCE_URL, headers={"Api-key": key}, json=user)
        assert resp.status_code == 204

        # Case 3
        resp = client.put(
            self.RESOURCE_URL, headers={"Api-key": key}, data="non-json data"
        )
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_user = _get_user(username=None)
        resp = client.put(
            self.RESOURCE_URL, headers={"Api-key": key}, json=invalid_user
        )
        assert resp.status_code == 400

        # Case 5
        resp = client.put(self.INVALID_URL, headers={"Api-key": key}, json=user)
        assert resp.status_code == 404

    def test_delete(self, client):
        """
        Tests delete method for user item.
        Case 1: Delete existing user -> 204
        Case 2: Delete previously deleted user -> 404
        Case 3: Delete non-existing resource -> 404
        """
        # Case 1
        key = _login(client)
        resp = client.delete(self.RESOURCE_URL, headers={"Api-key": key})
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
        Case 3: Logout non-existing user -> 404
        """
        # Case 1
        key = _login(client)
        resp = client.post(self.RESOURCE_URL, headers={"Api-key": key})
        assert resp.status_code == 200

        # Case 3
        resp = client.post(self.INVALID_URL)
        assert resp.status_code == 404


class TestReactionCollection(object):
    RESOURCE_URL = "/api/reactions/"

    def test_post(self, client):
        # Case 1
        # Check that reaction does not exist yet

        reaction = _get_reaction(reaction_type=9, user_id=1, message_id=1)
        resp = client.post(self.RESOURCE_URL, json=reaction)
        assert resp.status_code == 201

        # Check that reaction exists after posting it
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # Case 2
        reaction = _get_reaction(reaction_type=8, user_id=1, message_id=1)
        resp = client.post(self.RESOURCE_URL, json=reaction)
        assert resp.status_code == 409

        # Case 3
        resp = client.post(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_reaction = _get_reaction(
            reaction_type=None, user_id=None, message_id=None
        )
        resp = client.post(self.RESOURCE_URL, json=invalid_reaction)
        assert resp.status_code == 400


class TestReactionItem(object):
    RESOURCE_URL = "/api/reactions/2/"
    INVALID_URL = "/api/reactions/non-existing-reaction/"

    def test_get(self, client):
        """
        Tests get method for user item.
        Case 1: Get existing user -> 200
        Case 2: Get non-existing user -> 404
        """
        # Case 1
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert resp.headers["reaction"] == self.RESOURCE_URL.split("/")[-2]

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
        reaction = _get_reaction(reaction_type=1, user_id=1, message_id=1)
        # Case 1
        resp = client.put(self.RESOURCE_URL, json=reaction)
        assert resp.status_code == 204

        # Case 2
        reaction["reaction_type"] = 2
        resp = client.put(self.RESOURCE_URL, json=reaction)
        assert resp.status_code == 204

        # Case 3
        resp = client.put(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_reaction = reaction = _get_reaction(
            reaction_type=None, user_id=None, message_id=None
        )
        resp = client.put(self.RESOURCE_URL, json=invalid_reaction)
        assert resp.status_code == 400

        # Case 5
        resp = client.put(self.INVALID_URL, json=reaction)
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


class TestRequireLogin(object):
    RESOURCE_URL1 = "/api/users/user1/"
    RESOURCE_URL2 = "/api/users/user2/"

    def test_require_login(self, client):
        """
        Tests the functionality of the require_login decorator.
        Case 1: Delete user with correct API key -> 204
        Case 2: Delete user without connected API key -> 403
        Case 3: Delete user with incorrect API key -> 403
        Case 4: Delete user without API key -> 403
        """
        # Case 1
        key = _login(client)
        resp = client.delete(self.RESOURCE_URL1, headers={"Api-key": key})
        assert resp.status_code == 204

        # Case 2
        resp = client.delete(self.RESOURCE_URL2, headers={"Api-key": key})
        assert resp.status_code == 403

        # Case 3
        _login(client, username="user2", password="password")
        key = _login(client, username="user3", password="password")
        resp = client.delete(self.RESOURCE_URL2, headers={"Api-key": key})
        assert resp.status_code == 403

        # Case 4
        resp = client.delete(self.RESOURCE_URL2, headers={"Api-key": None})
        assert resp.status_code == 403


class TestThreadCollection(object):
    RESOURCE_URL = "/api/threads/"

    def test_post(self, client):
        """
        Tests posting to thread collection.
        Case 1: Valid thread posted -> 201
        Case 2: Non-json data posted -> 400/415
        Case 3: Invalid thread posted -> 400
        """
        thread = _get_thread()
        # Case 1
        resp = client.post(self.RESOURCE_URL, json=thread)
        assert resp.status_code == 201
        assert re.match(f"{self.RESOURCE_URL}thread-\\d/", resp.headers["Location"])
        # Check that user exists after posting it
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # Case 2
        resp = client.post(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 3
        invalid_thread = _get_thread(title=None)
        resp = client.post(self.RESOURCE_URL, json=invalid_thread)
        assert resp.status_code == 400


class TestThreadItem(object):
    RESOURCE_URL = "/api/threads/thread-1/"
    INVALID_URL = "/api/threads/non-existing-thread/"

    def test_get(self, client):
        """
        Tests get method for thread item.
        Case 1: Get existing thread -> 200
        Case 2: Get non-existing thread -> 404
        """
        # Case 1
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert resp.headers["title"] == "Thread title"

        # Case 2
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """
        Tests put method for thread item.
        Case 1: Put valid thread -> 204
        Case 2: Change existing thread's title -> 204
        Case 3: Put non-json data -> 400/415
        Case 4: Put invalid thread -> 400
        Case 5: Put to non-existing resource -> 404
        """
        thread = _get_thread()
        # Case 1
        resp = client.put(self.RESOURCE_URL, json=thread)
        assert resp.status_code == 204

        # Case 2
        thread["title"] = "new title"
        resp = client.put(self.RESOURCE_URL, json=thread)
        assert resp.status_code == 204

        # Case 3
        resp = client.put(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_thread = _get_thread(title=None)
        resp = client.put(self.RESOURCE_URL, json=invalid_thread)
        assert resp.status_code == 400

        # Case 5
        resp = client.put(self.INVALID_URL, json=thread)
        assert resp.status_code == 404

    def test_delete(self, client):
        """
        Tests delete method for thread item.
        Case 1: Delete existing thread -> 204
        Case 2: Delete previously deleted thread -> 404
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


class TestMessageCollection(object):
    RESOURCE_URL = "/api/messages/"

    def test_post(self, client):
        """
        Tests posting to message collection.
        Case 1: Valid message posted -> 201
        Case 2: Non-json data posted -> 400/415
        Case 3: Invalid message posted -> 400
        """
        message = _get_message()
        # Case 1
        resp = client.post(self.RESOURCE_URL, json=message)
        assert resp.status_code == 201
        print(resp.headers["Location"])
        assert re.match(f"{self.RESOURCE_URL}message-\\d/", resp.headers["Location"])
        # Check that user exists after posting it
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # Case 2
        resp = client.post(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 3
        invalid_message = _get_message(message_content=None)
        resp = client.post(self.RESOURCE_URL, json=invalid_message)
        assert resp.status_code == 400


class TestMessageItem(object):
    RESOURCE_URL = "/api/messages/message-1/"
    INVALID_URL = "/api/messages/non-existing-message/"

    def test_get(self, client):
        """
        Tests get method for message item.
        Case 1: Get existing message -> 200
        Case 2: Get non-existing message -> 404
        """
        # Case 1
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        assert resp.headers["message_content"] == "Thread opening message"

        # Case 2
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """
        Tests put method for message item.
        Case 1: Put valid message -> 204
        Case 2: Change existing message's content -> 204
        Case 3: Put non-json data -> 400/415
        Case 4: Put invalid message -> 400
        Case 5: Put to non-existing resource -> 404
        """
        message = _get_message()
        # Case 1
        resp = client.put(self.RESOURCE_URL, json=message)
        assert resp.status_code == 204

        # Case 2
        message["message_content"] = "New content"
        resp = client.put(self.RESOURCE_URL, json=message)
        assert resp.status_code == 204

        # Case 3
        resp = client.put(self.RESOURCE_URL, data="non-json data")
        assert resp.status_code in [400, 415]

        # Case 4
        invalid_message = _get_message(message_content=None)
        resp = client.put(self.RESOURCE_URL, json=invalid_message)
        assert resp.status_code == 400

        # Case 5
        resp = client.put(self.INVALID_URL, json=message)
        assert resp.status_code == 404

    def test_delete(self, client):
        """
        Tests delete method for message item.
        Case 1: Delete existing message -> 204
        Case 2: Delete previously deleted message -> 404
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


class TestMediaCollection(object):
    RESOURCE_URL = "/api/media/"
    INVALID_URL = "/api/mediaaaaaaaaa/"

    """
    Case1: Valid Post -> 201
    Case2: Invalid URL -> 404
    Case3: Non-json data -> 400/415
    Case4: Wrong method -> 405
    Case5: Invalid media_url -> 400
    Case6: Invalid media_url empty -> 400
    Case7: Too long media_url -> 400
    Case8: No message with that ID/Conflict -> 409
    """

    def test_post(self, client):
        test_picture = "https://upload.wikimedia.org/wikipedia/commons/5/51/Google.png"

        # Case1
        media = _get_media(media_url=test_picture, message_id=4)
        resp = client.post(self.RESOURCE_URL, json=media)
        assert resp.status_code == 201

        # Case2
        media = _get_media(media_url=test_picture, message_id=4)
        resp = client.post(self.INVALID_URL, json=media)
        assert resp.status_code == 404

        # Case3
        resp = client.post(self.RESOURCE_URL, json="non-json-data")
        assert resp.status_code in [400, 415]

        # Case4
        media = _get_media(media_url=test_picture, message_id=4)
        resp = client.get(self.RESOURCE_URL, json=media)
        assert resp.status_code == 405

        # Case5
        media = _get_media(
            media_url="https://upload.wikimedia.org/wikipedia/commons/5/51/Google",
            message_id=4,
        )
        resp = client.post(self.RESOURCE_URL, json=media)
        assert resp.status_code == 400

        # Case6
        media = _get_media(media_url="", message_id=4)
        resp = client.post(self.RESOURCE_URL, json=media)
        assert resp.status_code == 400

        # Case5
        too_long_url = "a" * 130 + ".png"
        media = _get_media(media_url=too_long_url, message_id=4)
        resp = client.post(self.RESOURCE_URL, json=media)
        assert resp.status_code == 400

        # Case8
        media = _get_media(media_url=test_picture, message_id=50000)
        resp = client.post(self.RESOURCE_URL, json=media)
        assert resp.status_code == 409


class TestMediaItem(object):
    VALID_URL = "/api/media/3/"
    INVALID_URL = "/api/media/23456/"

    def test_get(self, client):
        """
        Case1: Get valid media -> 200
        Case2: Get non-existing media -> 404
        """

        # Case1
        resp = client.get(self.VALID_URL)
        assert resp.status_code == 200

        # Case2
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """
        Case1: Valid Put -> 204
        Case2: Change message_id -> 204
        Case 3: Put non-json data -> 400/415
        Case 4: Put invalid media_url -> 400
        Case 5: Put to non-existing resource -> 404
        """

        test_picture = "https://upload.wikimedia.org/wikipedia/commons/5/51/Google.png"
        media = _get_media(media_url=test_picture, message_id=4)
        media1 = _get_media(media_url=test_picture, message_id=2)
        media2 = _get_media(media_url="aaaaa", message_id=4)

        # Case1
        resp = client.put(self.VALID_URL, json=media)
        assert resp.status_code == 204

        # Case2
        resp = client.put(self.VALID_URL, json=media1)

        assert resp.status_code == 204

        # Case3
        resp = client.put(self.VALID_URL, json="non-json-data")
        assert resp.status_code in [400, 415]

        # Case4
        resp = client.put(self.VALID_URL, json=media2)
        assert resp.status_code == 400

        # Case5
        resp = client.put(self.INVALID_URL, json=media)
        assert resp.status_code == 404

    def test_delete(self, client):
        """
        Case 1: Delete existing media -> 204
        Case 2: Delete previously deleted media -> 404
        Case 3: Delete non-existing media -> 404
        """

        # Case1
        resp = client.delete(self.VALID_URL)
        assert resp.status_code == 204

        # Case2
        resp = client.delete(self.VALID_URL)
        assert resp.status_code == 404

        # Case3
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
