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
    """
    Thread collection resource
    """
    def post(self):
        """
        POST method for thread collection.
        Creates a new thread with the request parameters and
        adds it to the database.
        :return:
            On successful thread creation, returns a response with
            the created thread's URI as a Location header,
            and status 201.
        """
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
    """
    Thread item resource
    """
    def get(self, thread):
    """
        GET method for thread item.
        Fetches the requested thread from the database.
        :param thread:
            The thread object that needs to be fetched from the database.
        :return:
            Returns a response with the fetched thread object's id and
            thread attributes in the headers and status 200.
     """
        return Response(headers=thread.serialize(), status=200)

    def put(self, thread):
        """
        PUT method for thread item.
        Rewrites an already existing thread object's attributes.
        :param thread:
            The thread object which is rewritten.
        :return:
            On successful rewrite, returns a response with status 204.
        """
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
        """
        DELETE method for thread item.
        Deletes an existing thread object from the database.
        :param thread:
            The thread object which is deleted.
        :return:
            Returns a response with status 204.
        """
        db.session.delete(thread)
        db.session.commit()
        return Response(status=204)


class ThreadConverter(BaseConverter):
    """
    Converter for thread URL variable.
    """
    def to_python(self, thread_id):
        """
        Converts the thread picked from URL to corresponding
        database thread object.
        :param thread_id:
            ID of the thread object in the database.
        :return:
            Returns the thread object fetched from the database.
        """
        id = thread_id.split("-")[-1]
        db_thread = Thread.query.filter_by(id=id).first()
        if db_thread is None:
            raise NotFound
        return db_thread

    def to_url(self, db_thread):
        """
        Uses the thread object's id to create a URI for the object.
        :param db_thread:
            The thread object that the URI is created for.
        :return:
            Returns the thread object's id attribute as the URI.
        """
        return f"thread-{db_thread.id}"
