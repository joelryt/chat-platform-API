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

from src.models import Thread, Message
from src.app import db

class ThreadItem(Resource):
    def post(self):
        if not request.json:
            abort(415)

        try:
            thread = Thread(
                id=request.json["id"],
                title=request.json["title"]
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
        return Response(json.dumps(body), 200)
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
        db_thread = Thread.query.filter_by(id=thread_id).first()
        if db_thread is None:
            raise NotFound
        return db_thread

    def to_url(self, db_thread):
        return str(db_thread.id)

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
        #thread.thread_id = thread
        db.session.add(thread)
        db.session.commit()
        thread_uri = api.url_for(ThreadItem, thread=thread)

        return Response(headers={"Location": thread_uri}, status=201)

#app.url_map.converters["thread"] = ThreadConverter