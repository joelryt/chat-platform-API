from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Message
from src.app import db


class MessageCollection(Resource):

    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Message.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        message = Message()
        message.deserialize(request.json)
        try:
            db.session.add(message)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Message with id {request.json['message_id']} already exists."
            ) from exc
        from src.api import api
        uri = api.url_for(MessageItem, message=message)
        return Response(headers={"Location": uri}, status=201)


class MessageItem(Resource):

    def get(self, message):
        return Response(headers=message.serialize(), status=200)

    def put(self, thread):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Message.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        message.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Message with id {request.json['message_id']} already exists."
            ) from exc
        return Response(status=204)




    def delete(self, message):
        db.session.delete(message)
        db.session.commit()
        return Response(status=204)


class MessageConverter(BaseConverter):

    def to_python(self, message_id):
        id = message_id.split("-")[-1]
        db_message = Message.query.filter_by(id=id).first()
        if db_message is None:
            raise NotFound
        return db_message

    def to_url(self, db_message):
        return f"thread-{db_message.message_id}"
