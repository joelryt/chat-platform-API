from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import User
from src.app import db


class UserCollection(Resource):

    # Register new user
    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                User.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        user = User()
        user.deserialize(request.json)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Username {request.json['username']} already exists."
            ) from exc
        from src.api import api
        uri = api.url_for(UserItem, user=user)
        return Response(headers={"Location": uri}, status=201)


class UserItem(Resource):

    def get(self, user):
        return Response(headers={"Username": user.username}, status=200)

    def put(self, user):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(
                request.json,
                User.json_schema()
            )
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        user.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Username {request.json['username']} already exists."
            ) from exc
        return Response(status=204)

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)


class UserConverter(BaseConverter):

    def to_python(self, username):
        db_user = User.query.filter_by(username=username).first()
        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, db_user):
        return db_user.username
