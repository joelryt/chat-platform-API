import secrets
from flask_restful import Resource
from flask import Response, request
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Unauthorized
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import User, ApiKey
from src.app import db


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
        key.key = ApiKey.key_hash(secrets.token_urlsafe())
        key.user = db_user
        try:
            db.session.add(key)
            db.session.commit()
        except IntegrityError:
            # Get the key that is already associated with the user
            key = ApiKey.query.filter_by(user=db_user).first()

        return Response(headers={"Api-key": key.key}, status=201)


class UserLogout(Resource):
    """
    Deletes the existing API connected to the user on logout.
    """
    def post(self, user):
        db_key = ApiKey.query.filter_by(user=user).first()
        if db_key is None:
            raise NotFound
        db.session.delete(db_key)
        db.session.commit()
        return Response(status=200)
