from flask import Blueprint
from flask_restful import Api
from src.resources.user import UserItem, UserCollection
from src.resources.auth import UserLogin, UserLogout

from src.resources.thread import ThreadItem
from src.resources.Message import MessageCollection, MessageItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(UserCollection, "/users/")
api.add_resource(UserLogin, "/login/")
api.add_resource(UserLogout, "/users/<user:user>/logout/")
api.add_resource(ThreadItem, "/api/threads/<thread:thread>/")
api.add_resource(MessageCollection, "/api/threads/<thread:thread>/messages/")
api.add_resource(
    MessageItem,
    "/api/threads/<thread:thread>/messages/<message:message>/"
)