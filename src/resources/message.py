import json
from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError, draft7_format_checker
from sqlalchemy.exc import IntegrityError

from src.models import Message
from src.app import db


class MessageCollection(Resource):
    """
    Message collection resource
    """

    def post(self, thread):
        """
        POST method for message collection.
        Creates a new message with the request parameters and
        adds it to the database.
        :return:
            On successful message creation, returns a response with
            the created message's URI as a Location header,
            and status 201.
        """
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
            Returns a response with a list of message_id attributes of all messages
            from the collection in the response body and status 200.
        """
        messages = Message.query.filter_by(thread=thread).all()
        message_collection = [message.message_id for message in messages]
        body = {"message_ids": message_collection}
        return Response(json.dumps(body), status=200, mimetype="application/json")


class MessageItem(Resource):
    """
    Message item resource.
    """

    def get(self, thread, message):
        """
        GET method for message item.
        Fetches the requested message from the database.
        :param message:
            The message object that needs to be fetched from the database.
        :param thread:
            The thread object that needs to be fetched from the database.
        :return:
            Returns a response with the fetched message object's id and
            message attributes in the headers and status 200.
        """
        return Response(headers=message.serialize(), status=200)

    def put(self, thread, message):
        """
        PUT method for message item.
        Rewrites an already existing message object's attributes.
        :param message:
            The message object which is rewritten.
        :param thread:
            The thread object which is affected.
        :return:
            On successful rewrite, returns a response with status 204.
        """
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
        """
        DELETE method for message item.
        Deletes an existing message object from the database.
        :param message:
            The message object that is being deleted.
        :param thread:
            The thread object of which message is deleted.
        :return:
            Returns a response with status 204.
        """
        db.session.delete(message)
        db.session.commit()
        return Response(status=204)


class MessageConverter(BaseConverter):
    """
    Converter for message URL variable.
    """

    def to_python(self, message_id):
        """
        Converts the message picked from URL to corresponding
        database message object.
        :param message_id:
            ID of the message object in the database.
        :return:
            Returns the message object fetched from the database.
        """
        id = message_id.split("-")[-1]
        db_message = Message.query.filter_by(message_id=id).first()
        if db_message is None:
            raise NotFound
        return db_message

    def to_url(self, db_message):
        """
        Uses the message object's id to create a URI for the object.
        :param db_message:
            The message object that the URI is created for.
        :return:
            Returns the message object's id attribute as the URI.
        """
        return f"message-{db_message.message_id}"
