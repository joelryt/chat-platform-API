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
        return str(db_message.id)

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

#app.url_map.converters["message"] = MessageConverter