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
    def post(self, message, thread):
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
        reactions = Reaction.query.filter_by(message=message).all()
        reaction_collection = [reaction.reaction_id for reaction in reactions]
        body = {"reaction_ids": reaction_collection}
        return Response(json.dumps(body), status=200, mimetype="application/json")


class ReactionItem(Resource):
    def get(self, reaction, message, thread):
        response_data = reaction.serialize()
        response_data["reaction"] = str(reaction.reaction_id)
        return Response(headers=response_data, status=200)

    def delete(self, reaction, message, thread):
        db.session.delete(reaction)
        db.session.commit()
        return Response(status=204)

    def put(self, reaction, message, thread):
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
    def to_python(self, reaction_id):
        db_reaction = Reaction.query.filter_by(reaction_id=reaction_id).first()
        if db_reaction is None:
            raise NotFound
        return db_reaction

    def to_url(self, db_reaction):
        return str(db_reaction.reaction_id)
