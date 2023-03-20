import json
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
            validate(request.json, Thread.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        thread = Thread()
        thread.deserialize(request.json)
        try:
            db.session.add(thread)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict() from exc
        from src.api import api

        uri = api.url_for(ThreadItem, thread=thread)
        return Response(headers={"Location": uri}, status=201)

    def get(self):
        """
        GET method for thread collection.
        Fetches all thread objects from database.
        :return:
            Returns a response with a list of thread_id attributes of all threads
            in the response body and status 200.
        """
        threads = Thread.query.all()
        thread_collection = [thread.id for thread in threads]
        body = {"thread_ids": thread_collection}
        return Response(json.dumps(body), status=200, mimetype="application/json")


class ThreadItem(Resource):
    def get(self, thread):
        return Response(headers=thread.serialize(), status=200)

    def put(self, thread):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Thread.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        thread.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict() from exc
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
