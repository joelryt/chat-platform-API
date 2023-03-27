import json
from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Media
from src.app import db


class MediaCollection(Resource):
    """
    Media collection resource
    """
    def post(self, message, thread):
        """
        POST method for media collection.
        creates media that is linked to a message and adds it to the database
        :param message:
            The message object the media belongs to.
        :param thread:
            The thread object the media's parent message belongs to.
        :return:
            On successful media creation, returns a response with
            the created media's URI as a Location header,
            and status 201.
        """
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Media.json_schema())
        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        media = Media()
        media.deserialize(request.json)
        try:
            db.session.add(media)
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(description=str(exc)) from exc
        from src.api import api

        uri = api.url_for(MediaItem, media=media, message=message, thread=thread)
        return Response(headers={"Location": uri}, status=201)
    
    def get(self, message, thread):
        """
        GET method for media collection.
        Fetches all media from a selected message.
        :param thread:
            thread where the media needs to be extracted from
        :param message:
            message where the media needs to be extracted from
        :return:
            Returns a list with the media_ids of media contained
            in the selected thread and status 200.
        """
        thread_media = Media.query.filter_by(message=message).all()
        media_collection = [media.media_id for media in thread_media]
        body = {"media_ids": media_collection}
        return Response(json.dumps(body), status=200, mimetype="application/json")



class MediaItem(Resource):
    """
    Media item resource
    """
    def get(self, media, message, thread):
        """
        GET method for media items
        Fetches media from the database
        :param media:
            media that is needed from the database
        :param message:
            message that is the parent of the needed media
        :param thread:
            parent thread of the message containing the needed media
        :return:
            returns with id, url, and message_id of the target media and status 200
        """
        response_data = media.serialize()
        response_data["media"] = str(media.media_id)
        return Response(headers=response_data, status=200)

    def put(self, media, message, thread):
        """
        PUT method for media items
        Enables the editing of media
        :param media:
            media to be edited
        :param message:
            parent message of the media
        :param thread:
            parent thread of the message
        :return:
            returns status 204 upon successful edit
        """
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Media.json_schema())

        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc

        media.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(description=str(exc)) from exc
        return Response(status=204)

    def delete(self, media, message, thread):
        """
        DELETE method for media items
        Enables deletion of media items
        :param media:
            media to be deleted
        :param message:
            parent message of the media
        :param thread:
            parent thread of the message
        :return:
            returns status 204 upon successful deletion
        """
        db.session.delete(media)
        db.session.commit()
        return Response(status=204)


class MediaConverter(BaseConverter):
    """
    Converter for Media resources
    """
    def to_python(self, media_id):
        """
        Converts the media picked from URL to corresponding
        database user object.
        :param media_id:
            media id of the media object in the database
        :return:
            returns media object from the database
        """
        db_media = Media.query.filter_by(media_id=media_id).first()
        if db_media is None:
            raise NotFound
        return db_media

    def to_url(self, db_media):
        """
        Uses media id to create a URI for the media object
        :param db_media:
            media object that the URI is created for
        :return:
            Returns the media object's media_id attribute as the URI
        """
        return str(db_media.media_id)
