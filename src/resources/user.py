from flask_restful import Resource
from flask import Response
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound
from src.models import User
from src.app import db


class UserItem(Resource):

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
