import datetime
from src.app import db
from src.models import Thread, Message, User, Reaction, Media


def sample_database():
    """
    Creates a small sample database.

    thread
    |
    message1 - user1, reaction1, media1
    |
    --message2 - user2, reaction2
    |    |
    |    --message3 - user1, media2
    |
    --message4 - user3, reaction3, media3

    """
    user1 = User(username="user1", password=User.password_hash("password"))
    user2 = User(username="user2", password=User.password_hash("password"))
    user3 = User(username="user3", password=User.password_hash("password"))

    thread = Thread(title="Thread title")
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

    message4 = Message(
        message_content="Reply3",
        timestamp=datetime.datetime.now()
    )
    message4.user = user3
    message4.thread = thread
    message4.parent = message1
    media3 = Media(media_url="media3/url/")
    media3.message = message4
    reaction3 = Reaction(reaction_type=1)
    reaction3.user = user1
    reaction3.message = message4

    db.session.add(user1)
    db.session.add(user2)
    db.session.add(user3)
    db.session.add(thread)
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
