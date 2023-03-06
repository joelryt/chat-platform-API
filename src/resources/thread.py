from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Thread
from src.app import db


class ThreadCollection(Resource):

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
                f"Thread with id {request.json['id']} already exists."
            ) from exc
        from src.api import api
        uri = api.url_for(ThreadItem, thread=thread)
        return Response(headers={"Location": uri}, status=201)


class ThreadItem(Resource):

    def get(self, thread):
        return Response(headers=thread.serialize(), status=200)

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
                f"Thread with id {request.json['id']} already exists."
            ) from exc
        return Response(status=204)

    def delete(self, thread):
        db.session.delete(thread)
        db.session.commit()
        return Response(status=204)


class ThreadConverter(BaseConverter):

    def to_python(self, thread_id):
        id = thread_id.split("-")[-1]
        db_thread = Thread.query.filter_by(id=id).first()
        if db_thread is None:
            raise NotFound
        return db_thread

    def to_url(self, db_thread):
        return f"thread-{db_thread.id}"
