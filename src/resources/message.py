import flask.json
from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError, draft7_format_checker
from sqlalchemy.exc import IntegrityError

from src.models import Message
from src.app import db


class MessageCollection(Resource):
    def post(self, thread):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Message.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        message = Message()
        message.deserialize(request.json)
        message.thread = thread
        try:
            db.session.add(message)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict() from exc
        from src.api import api

        uri = api.url_for(MessageItem, message=message, thread=thread)
        return Response(headers={"Location": uri}, status=201)

    def get(self, thread):
        """
        GET method for message collection.
        Fetches all the message objects belonging to the message collection
        from database.
        :param thread:
            Thread object from which the message collection is fetched from.
        :return:
            Returns list of message_id attributes of all messages
            from the collection.
        """
        messages = Message.query.filter_by(thread=thread).all()
        message_collection = [message.message_id for message in messages]
        return message_collection, 200


class MessageItem(Resource):
    def get(self, thread, message):
        return Response(headers=message.serialize(), status=200)

    def put(self, thread, message):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Message.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        message.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict() from exc
        return Response(status=204)

    def delete(self, thread, message):
        db.session.delete(message)
        db.session.commit()
        return Response(status=204)


class MessageConverter(BaseConverter):
    def to_python(self, message_id):
        id = message_id.split("-")[-1]
        db_message = Message.query.filter_by(message_id=id).first()
        if db_message is None:
            raise NotFound
        return db_message

    def to_url(self, db_message):
        return f"message-{db_message.message_id}"
