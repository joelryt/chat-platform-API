from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Thread
from src.app import db


class ThreadCollection(Resource):

    # Register new thread
    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Thread.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        thread = Thread()
        thread.deserialize(request.json)
        try:
            db.session.add(thread)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Thread {request.json['thread']} already exists."
            ) from exc
        from src.api import api
        uri = api.url_for(ThreadItem, thread=thread)
        return Response(headers={"Location": uri}, status=201)


class ThreadItem(Resource):

    def get(self, thread):
        response_data = thread.serialize()
        response_data["thread"] = str(thread.thread_id)
        return Response(headers=response_data, status=200)

    def put(self, thread):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                Thread.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        thread.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Thread {request.json['thread']} already exists."
            ) from exc
        return Response(status=204)

    def delete(self, thread):
        db.session.delete(thread)
        db.session.commit()
        return Response(status=204)


class ThreadConverter(BaseConverter):

    def to_python(self, thread_id):
        db_thread = Thread.query.filter_by(id=thread_id).first()
        if db_thread is None:
            raise NotFound
        return db_thread

    def to_url(self, db_thread):
        return str(db_thread.thread)