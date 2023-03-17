from flask import Blueprint
from flask_restful import Api
from src.resources.user import UserItem, UserCollection
from src.resources.reaction import ReactionItem, ReactionCollection
from src.resources.thread import ThreadItem, ThreadCollection
from src.resources.message import MessageItem, MessageCollection
from src.resources.media import MediaCollection, MediaItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(UserCollection, "/users/")
api.add_resource(ReactionItem, "/threads/<thread:thread>/messages/<message:message>/reactions/<reaction:reaction>/")
api.add_resource(ReactionCollection, "/threads/<thread:thread>/messages/<message:message>/reactions/")
api.add_resource(ThreadCollection, "/threads/")
api.add_resource(ThreadItem, "/threads/<thread:thread>/")
api.add_resource(MessageCollection, "/threads/<thread:thread>/messages/")
api.add_resource(MessageItem, "/threads/<thread:thread>/messages/<message:message>/")
api.add_resource(MediaCollection, "/media/")
api.add_resource(MediaItem, "/media/<media:media>/")
