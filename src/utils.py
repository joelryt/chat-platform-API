import datetime
import secrets
from flask import request
from werkzeug.exceptions import Forbidden
from src.app import db
from src.models import Thread, Message, User, Reaction, Media, ApiKey

# API keys to be used in the sample database that can be used in testing
KEY1 = secrets.token_urlsafe()
KEY2 = secrets.token_urlsafe()
KEY3 = secrets.token_urlsafe()


def sample_database():
    """
    Creates a small sample database.

    thread1
    |
    message1 - user1, reaction1, media1
    |
    --message2 - user2, reaction2
    |    |
    |    --message3 - user1, media2
    |
    --message4 - user3, reaction3, media3

    thread2
    |
    message5 - user2, reaction4, reaction5
    |
    --message6 - user1
    |
    --message7 - user3, media4
        |
        --message8 - user2, reaction6

    thread3
    |
    message9 - user3, reaction7, media5
    |
    --message10 - user2, reaction8
        |
        --message11, user3, reaction9
    """
    user1 = User(username="user1", password=User.password_hash("password"))
    user2 = User(username="user2", password=User.password_hash("password"))
    user3 = User(username="user3", password=User.password_hash("password"))

    key1 = ApiKey(key=ApiKey.key_hash(KEY1))
    key1.user = user1
    key2 = ApiKey(key=ApiKey.key_hash(KEY2))
    key2.user = user2
    key3 = ApiKey(key=ApiKey.key_hash(KEY3))
    key3.user = user3

    # Thread 1
    thread1 = Thread(title="Thread title 1")
    message1 = Message(
        message_content="Thread opening message",
        timestamp=datetime.datetime.now(),
    )
    message1.user = user1
    message1.thread = thread1
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
    message2.thread = thread1
    message2.parent = message1
    reaction2 = Reaction(reaction_type=2)
    reaction2.user = user1
    reaction2.message = message2

    message3 = Message(
        message_content="Reply 2",
        timestamp=datetime.datetime.now(),
    )
    message3.user = user1
    message3.thread = thread1
    message3.parent = message2
    media2 = Media(media_url="media2/url/")
    media2.message = message3

    message4 = Message(message_content="Reply 3", timestamp=datetime.datetime.now())
    message4.user = user3
    message4.thread = thread1
    message4.parent = message1
    media3 = Media(media_url="media3/url/")
    media3.message = message4
    reaction3 = Reaction(reaction_type=1)
    reaction3.user = user1
    reaction3.message = message4

    db.session.add(user1)
    db.session.add(user2)
    db.session.add(user3)
    db.session.add(thread1)
    db.session.add(message1)
    db.session.add(media1)
    db.session.add(reaction1)
    db.session.add(message2)
    db.session.add(reaction2)
    db.session.add(message3)
    db.session.add(media2)
    db.session.add(message4)
    db.session.add(media3)
    db.session.add(reaction3)
    db.session.commit()

    # Thread 2
    thread2 = Thread(title="Thread title 2")
    message5 = Message(
        message_content="Thread opening message",
        timestamp=datetime.datetime.now(),
    )
    message5.user = user2
    message5.thread = thread2
    reaction4 = Reaction(reaction_type=1)
    reaction4.user = user1
    reaction4.message = message5
    reaction5 = Reaction(reaction_type=1)
    reaction5.user = user3
    reaction5.message = message5

    message6 = Message(
        message_content="Reply 1",
        timestamp=datetime.datetime.now(),
    )
    message6.user = user1
    message6.thread = thread2
    message6.parent = message5

    message7 = Message(message_content="Reply 2", timestamp=datetime.datetime.now())
    message7.user = user3
    message7.thread = thread2
    message7.parent = message5
    media4 = Media(media_url="media4/url/")
    media4.message = message7

    message8 = Message(message_content="Reply 3", timestamp=datetime.datetime.now())
    message8.user = user2
    message8.thread = thread2
    message8.parent = message7
    reaction6 = Reaction(reaction_type=1)
    reaction6.user = user1
    reaction6.message = message8

    db.session.add(thread2)
    db.session.add(message5)
    db.session.add(message6)
    db.session.add(message7)
    db.session.add(message8)
    db.session.add(reaction4)
    db.session.add(reaction5)
    db.session.add(reaction6)
    db.session.add(media4)
    db.session.commit()

    # Thread 3
    thread3 = Thread(title="Thread title 3")
    message9 = Message(
        message_content="Thread opening message",
        timestamp=datetime.datetime.now(),
    )
    message9.user = user3
    message9.thread = thread3
    reaction7 = Reaction(reaction_type=1)
    reaction7.user = user1
    reaction7.message = message9
    media5 = Media(media_url="media5/url/")
    media5.message = message9

    message10 = Message(
        message_content="Reply 1",
        timestamp=datetime.datetime.now(),
    )
    message10.user = user2
    message10.thread = thread3
    message10.parent = message9
    reaction8 = Reaction(reaction_type=1)
    reaction8.user = user3
    reaction8.message = message10

    message11 = Message(
        message_content="Reply 2",
        timestamp=datetime.datetime.now(),
    )
    message11.user = user3
    message11.thread = thread3
    message11.parent = message10
    reaction9 = Reaction(reaction_type=1)
    reaction9.user = user2
    reaction9.message = message11

    db.session.add(thread3)
    db.session.add(message9)
    db.session.add(message10)
    db.session.add(message11)
    db.session.add(reaction7)
    db.session.add(reaction8)
    db.session.add(reaction9)
    db.session.add(media5)
    db.session.commit()


# Modified from Exercise 2 Validating Keys example
# https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/#validating-keys
def require_authentication(func):
    """
    Authentication decorator for resource methods.
    Checks that the request headers contain correct API key related
    to the user object that is being accessed.
    """

    def wrapper(self, user, *args, **kwargs):
        try:
            token = request.headers["Api-key"].strip()
        except KeyError:
            raise Forbidden
        key_hash = ApiKey.key_hash(token)
        db_key = ApiKey.query.filter_by(user=user).first()
        if db_key is not None and secrets.compare_digest(key_hash, db_key.key):
            return func(self, user, *args, **kwargs)
        raise Forbidden

    return wrapper
