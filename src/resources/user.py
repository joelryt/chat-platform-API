import secrets
from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import User, ApiKey
from src.app import db
from src.utils import require_authentication


class UserCollection(Resource):
    """
    User collection resource.
    """

    def post(self):
        """
        POST method for user collection.
        Creates a new user with the request parameters and
        adds it to the database.
        Creates the API key for the user and adds it to the database.
        :return:
            On successful user creation, returns a response with
            the created user's URI as a Location header,
            the created API key as an API-key header,
            and status 201.
        """
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        user = User()
        user.deserialize(request.json)
        key = ApiKey()
        token = secrets.token_urlsafe()
        key.key = ApiKey.key_hash(token)
        key.user = user
        try:
            db.session.add(user)
            db.session.add(key)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(
                f"Username {request.json['username']} already exists."
            ) from exc
        from src.api import api

        uri = api.url_for(UserItem, user=user)
        return Response(headers={"Location": uri, "Api-key": token}, status=201)


class UserItem(Resource):
    """
    User item resource.
    """

    def get(self, user):
        """
        GET method for user item.
        Fetches the requested user from the database.
        :param user:
            The user object that needs to be fetched from the database.
        :return:
            Returns a response with the fetched user object's id and
            username attributes in the headers and status 200.
        """
        return Response(headers=user.serialize(), status=200)

    @require_authentication
    def put(self, user):
        """
        PUT method for user item.
        Rewrites an already existing user object's attributes.
        Requires authentication.
        :param user:
            The user object whose attributes are being rewritten.
        :return:
            On successful rewrite, returns a response with status 204.
        """
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, User.json_schema())
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

    @require_authentication
    def delete(self, user):
        """
        DELETE method for user item.
        Deletes an existing user object from the database.
        Requires authentication.
        :param user:
            The user object that is being deleted.
        :return:
            Returns a response with status 204.
        """
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)


class UserConverter(BaseConverter):
    """
    Converter for user URL variable.
    """

    def to_python(self, username):
        """
        Converts the username picked from URL to corresponding
        database user object.
        :param username:
            Username of the user object in the database.
        :return:
            Returns the user object fetched from the database.
        """
        db_user = User.query.filter_by(username=username).first()
        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, db_user):
        """
        Uses the user object's username to create a URI for the object.
        :param db_user:
            The user object that the URI is created for.
        :return:
            Returns the user object's username attribute as the URI.
        """
        return db_user.username
