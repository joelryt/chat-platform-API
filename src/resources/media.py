from flask_restful import Resource
from flask import Response, request
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, UnsupportedMediaType, BadRequest, Conflict
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError

from src.models import Media
from src.app import db


class MediaCollection(Resource):

    def post(self):
        if not request.json:
            raise UnsupportedMediaType
        
        try:
            validate(
                request.json,
                Media.json_schema()
            )
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
        uri = api.url_for(MediaItem, media=media)
        return Response(headers={"Location": uri}, status=201)
        
    
class MediaItem(Resource):

    def get(self, media):
        response_data = media.serialize()
        response_data["media"] = str(media.media_id)
        return Response(headers=response_data, status=200)
    
    def put(self, media):
        if not request.json:
            raise UnsupportedMediaType
        
        try:
            validate(
                request.json,
                Media.json_schema()
            )

        except ValidationError as exc:
            raise BadRequest(description=str(exc)) from exc
        
        media = Media()
        media.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as exc:
            raise Conflict(description=str(exc)) from exc
        return Response(status=204)
        
    def delete(self, media):
        db.session.delete(media)
        db.session.commit()
        return Response(status=204)

    
class MediaConverter(BaseConverter):
    def to_python(self, media_id):
        db_media = Media.query.filter_by(media_id=media_id).first()
        if db_media is None:
            raise NotFound
        return db_media
    
    def to_url(self, db_media):
        return str(db_media.media_id)

#API
#app.url_map.converters["media"] = MediaConverter
#api.add_resource(MediaCollection, "/api/media/")
#api.add_resource(MediaItem, "/api/media/<media:media>/")

#models
#class Media(db.Model):
#    media_id = db.Column(db.Integer, primary_key=True)
#    media_url = db.Column(db.String(128), nullable=False)
#    message_id = db.Column(db.Integer, db.ForeignKey("message.message_id", ondelete="CASCADE"), nullable=False)

#    message = db.relationship("Message", back_populates="media")

