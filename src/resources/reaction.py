import json
from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Reaction
from src.app import db


class ReactionCollection(Resource):
    """
    Reaction collection resource.
    """
    def post(self, message, thread):
        """
        POST method for reaction collection.
        Creates a new reaction with the request parameters and
        adds it to the database.
        :param message:
            The message object the reaction belongs to.
        :param thread:
            The thread object the reaction's parent message belongs to.
        :return:
            On successful reaction creation, returns a response with
            the created reaction's URI as a Location header,
            and status 201.
        """
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reaction.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc))
        reaction = Reaction()
        reaction.deserialize(request.json)
        # Check if reaction already exists
        existing_reaction = Reaction.query.filter_by(
            user_id=reaction.user_id, message_id=reaction.message_id
        ).first()
        if existing_reaction is not None:
            raise Conflict(
                f"User {reaction.user_id} has already reacted to the message with id {reaction.message_id}"
            )
        try:
            db.session.add(reaction)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Reaction with id {request.json['reaction_id']} already exists"
            ) from exc
        from src.api import api

        aaa = api.url_for(
            ReactionItem, reaction=reaction, message=message, thread=thread
        )
        return Response(headers={"Location": aaa}, status=201)

    def get(self, message, thread):
        """
        GET method for reaction collection.
        Fetches the reactions to a message from the database.
        :param message:
            The message object the reactions belong to.
        :param thread:
            The thread object the reactions' parent message belongs to.
        :return:
            Returns a list with the reaction_ids of the reactions to the
            message and status 200.
        """
        reactions = Reaction.query.filter_by(message=message).all()
        reaction_collection = [reaction.reaction_id for reaction in reactions]
        body = {"reaction_ids": reaction_collection}
        return Response(json.dumps(body), status=200, mimetype="application/json")


class ReactionItem(Resource):
    """
    Reaction item resource.
    """

    def get(self, reaction, message, thread):
        """
        GET method for reaction item.
        Fetches the requested reaction from the database.
        :param message:
            The message object the reaction belongs to.
        :param thread:
            The thread object the reaction's parent message belongs to.
        :param reaction:
            The reaction object that needs to be fetched from the database.
        :return:
            Returns a response with the fetched reaction object's id, type,
            message_id and user_id attributes in the headers and status 200.
        """
        response_data = reaction.serialize()
        return Response(headers=response_data, status=200)

    def delete(self, reaction, message, thread):
        """
        DELETE method for reaction item.
        Deletes an existing reaction object from the database.
        :param message:
            The message object the reaction belongs to.
        :param thread:
            The thread object the reaction's parent message belongs to.
        :param reaction:
            The reaction object that is being deleted.
        :return:
            Returns a response with status 204.
        """
        db.session.delete(reaction)
        db.session.commit()
        return Response(status=204)

    def put(self, reaction, message, thread):
        """
        PUT method for reaction item.
        Rewrites an already existing reaction object's attributes.
        :param message:
            The message object the reaction belongs to.
        :param thread:
            The thread object the reaction's parent message belongs to.
        :param reaction:
            The reaction object whose attributes are being rewritten.
        :return:
            On successful rewrite, returns a response with status 204.
        """
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reaction.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc
        reaction.deserialize(request.json)
        try:
            db.session.add(reaction)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Reaction with id {request.json['reaction_id']} already exists"
            ) from exc
        return Response(status=204)


class ReactionConverter(BaseConverter):
    """
    Converter for reaction URL variable.
    """
    def to_python(self, reaction_id):
        """
        Converts the reaction picked from URL to corresponding
        database user object.
        :param reaction_id:
            Id of the reaction object in the database.
        :return:
            Returns the reaction object fetched from the database.
        """
        db_reaction = Reaction.query.filter_by(reaction_id=reaction_id).first()
        if db_reaction is None:
            raise NotFound
        return db_reaction

    def to_url(self, db_reaction):
        """
        Uses the reaction object's id to create a URI for the object.
        :param reaction:
            The reaction object that the URI is created for.
        :return:
            Returns the reaction object's id attribute as the URI.
        """
        return str(db_reaction.reaction_id)
