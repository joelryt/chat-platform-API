import click
import hashlib
from src.app import db
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import datetime
from flask import Flask, request, Response, abort, json
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Api, Resource
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from werkzeug.routing import BaseConverter
from jsonschema import validate, ValidationError, draft7_format_checker

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Thread(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    messages = db.relationship("Message", back_populates="thread", cascade="all, delete, delete-orphan")


class Message(db.Model):
    message_id = db.Column(db.Integer, unique=True, primary_key=True)
    message_content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    thread_ID = db.Column(db.Integer, db.ForeignKey('thread.id', ondelete="CASCADE"), nullable=False)
    parent_ID = db.Column(db.Integer, db.ForeignKey('message.message_id', ondelete="CASCADE"))

    parent = db.relationship("Message", remote_side=[message_id])
    thread = db.relationship("Thread", back_populates="messages")
    reactions = db.relationship("Reaction", back_populates="message", cascade="all, delete")
    media = db.relationship("Media", back_populates="message", cascade="all, delete")
    user = db.relationship("User", back_populates="messages")


class User(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(db.String(32), nullable=False)

    messages = db.relationship("Message", back_populates="user", cascade="all, delete")
    reactions = db.relationship("Reaction", back_populates="user", cascade="all, delete")
    key = db.relationship("ApiKey", back_populates="user", uselist=False)

    def deserialize(self, doc):
        self.username = doc["username"]
        self.password = self.password_hash(doc["password"])

    @staticmethod
    def password_hash(password):
        return hashlib.sha256(password.encode()).digest()

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["username", "password"]
        }
        props = schema["properties"] = {}
        props["username"] = {
            "description": "Unique username for the user",
            "type": "string"
        }
        props["password"] = {
            "description": "Password for the user",
            "type": "string"
        }
        return schema


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


class ApiKey(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True)

    user = db.relationship("User", back_populates="key")

    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()


@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()


@click.command("populate-db")
def populate_db():
    from src.utils import sample_database
    sample_database()

class ThreadItem(Resource):
    def post(self):
        if not request.json:
            abort(415)

        try:
            thread = Thread(
                id=request.json["id"],
            )
            db.session.add(thread)
            db.session.commit()
        except KeyError:
            abort(400)
        except IntegrityError:
            abort(409)

        return "", 201
    def get(thread, id=None):
        if id is not None:
            thread_obj = Thread.query.join(id).filter(
                Thread.id == id
            ).first()
            messages_obj = Message.query.filter_by(
                thread_ID=thread_obj
            ).order_by("timestamp")
            body = {
                "thread": thread_obj.id,
                "messages": []
            }
            body["messages"].append(
                {
                    "message_id": messages_obj.message_id,
                    "message_content": messages_obj.message_content,
                    "timestamp": messages_obj.timestamp.isoformat(),
                    "sender": messages_obj.sender,
                    "thread_ID": messages_obj.thread_ID,
                    "parent_ID": messages_obj.parent_ID,
                }
            )
        else:
            raise NotFound
        return Response(json.dumps(body), 200, mimetype=JSON)
    def delete(self, id=None):
        if id is not None:
            thread = Thread.query.get(id)
            db.session.delete(thread)
            db.session.commit()

    def serialize(self):
        return {
            "id": self.id,
        }
    def deserialize(self, doc):
        self.id = doc["id"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["id"]
        }
        props = schema["properties"] = {}
        props["id"] = {
            "type": "integer"
        }
        return schema

class ThreadConverter(BaseConverter):
    def to_python(self, thread_id):
        db_thread = Thread.query.filter_by(name=thread_id).first()
        if db_thread is None:
            raise NotFound
        return db_thread

    def to_url(self, db_thread):
        return db_thread.id

class MessageItem(Resource):
    def post(self):
        if not request.json:
            abort(415)

        try:
            message = Message(
                temp=request.json["temp"],
            )
            db.session.add(message)
            db.session.commit()
        except KeyError:
            abort(400)
        except IntegrityError:
            abort(409)

        return "", 201
    def get(self, id=None):
        if id is not None:
            messages_obj = Message.query.filter_by(
                message_id=id
            ).order_by("timestamp")
            body = {
                "message": id,
                "details": []
            }
            body["details"].append(
                {
                    "message_id": messages_obj.message_id,
                    "message_content": messages_obj.message_content,
                    "timestamp": messages_obj.timestamp.isoformat(),
                    "sender": messages_obj.sender,
                    "thread_ID": messages_obj.thread_ID,
                    "parent_ID": messages_obj.parent_ID,
                }
            )
        else:
            raise NotFound
        return Response(json.dumps(body), 200, mimetype=JSON)
    def delete(self, message_id=None):
        if message_id is not None:
            message = Message.query.get(message_id)
            db.session.delete(message)
            db.session.commit()
    def put(self, message):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Message.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        message.deserialize(request.json)
        try:
            db.session.add(message)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Message with id '{message_id}' already exists.".format(
                    **request.json
                )
            )

        return Response(status=204)

    def serialize(self):
        return {
            "message_id": self.message_id,
        }

    def deserialize(self, doc):
        self.message_id = doc["message_id"]
        self.message_content = doc["message_content"]
        self.timestamp = datetime.datetime.fromisoformat(doc["temp"])
        self.thread_ID = doc["thread_ID"]
        self.parent_ID = doc["parent_ID"]
    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["message_id", "message_content", "timestamp",
                         "sender", "thread_ID", "parent_ID"]
        }
        props = schema["properties"] = {}
        props["message_id"] = {
            "type": "integer"
        }
        props["message_content"] = {
            "type": "string"
        }
        props["timestamp"] = {
            "type": "datetime"
        }
        props["sender"] = {
            "type": "string"
        }
        props["thread_ID"] = {
            "type": "integer"
        }
        props["parent_ID"] = {
            "type": "integer"
        }
        return schema

class MessageConverter(BaseConverter):
    def to_python(self, message_id):
        db_message = Message.query.filter_by(name=message_id).first()
        if db_message is None:
            raise NotFound
        return db_message

    def to_url(self, db_message):
        return db_message.id

class MessageCollection(Resource):

    def post(self, message):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Message.json_schema(),
                format_checker=draft7_format_checker
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        message = Message()
        message.deserialize(request.json)
        message.message_id = message #HOOOOOOX
        db.session.add(message)
        db.session.commit()
        message_uri = api.url_for(MessageItem, message=message)

        return Response(headers={"Location": message_uri}, status=201)

class ThreadCollection(Resource):

    def post(self, thread):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Thread.json_schema(),
                format_checker=draft7_format_checker
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        thread = Thread()
        thread.deserialize(request.json)
        thread.thread_id = thread #HOOOOOOX
        db.session.add(thread)
        db.session.commit()
        thread_uri = api.url_for(ThreadItem, thread=thread)

        return Response(headers={"Location": thread_uri}, status=201)
app.url_map.converters["thread"] = ThreadConverter
app.url_map.converters["message"] = MessageConverter