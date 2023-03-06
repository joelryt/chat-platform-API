import secrets
from flask_restful import Resource
from flask import Response, request
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Unauthorized
from jsonschema import validate, ValidationError
from werkzeug.exceptions import Forbidden

from src.models import User, ApiKey
from src.app import db


# Modified from Exercise 2 Validating Keys example
# https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/#validating-keys
def require_login(func):
    def wrapper(self, user, *args, **kwargs):
        try:
            print('Api-key:', request.headers["Api-key"])
            token = request.headers["Api-key"].strip()
        except KeyError:
            raise Forbidden
        key_hash = ApiKey.key_hash(token)
        db_key = ApiKey.query.filter_by(user=user).first()
        if db_key is not None and secrets.compare_digest(key_hash, db_key.key):
            return func(self, user, *args, **kwargs)
        raise Forbidden
    return wrapper


class UserLogin(Resource):
    """
    Creates a new API key for the user on login.
    """
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

        db_user = User.query.filter_by(username=request.json["username"]).first()
        if db_user is None:
            raise NotFound
        if User.password_hash(request.json["password"]) != db_user.password:
            raise Unauthorized

        key = ApiKey()
        token = secrets.token_urlsafe()
        key.key = ApiKey.key_hash(token)
        key.user = db_user
        db.session.add(key)
        db.session.commit()

        return Response(headers={"Api-key": token}, status=201)


class UserLogout(Resource):
    """
    Deletes the existing API key connected to the user on logout.
    """
    @require_login
    def post(self, user):
        db_key = ApiKey.query.filter_by(user=user).first()
        if db_key is None:
            raise NotFound
        db.session.delete(db_key)
        db.session.commit()
        return Response(status=200)
