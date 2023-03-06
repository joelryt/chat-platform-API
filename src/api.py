from flask import Blueprint
from flask_restful import Api
from src.resources.user import UserItem, UserCollection
from src.resources.auth import UserLogin, UserLogout
from src.resources.reaction import ReactionItem, ReactionCollection
from src.resources.thread import ThreadItem, ThreadCollection

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(UserItem, "/users/<user:user>/")
api.add_resource(UserCollection, "/users/")
api.add_resource(UserLogin, "/login/")
api.add_resource(UserLogout, "/users/<user:user>/logout/")
api.add_resource(ReactionItem, "/reactions/<reaction:reaction>/")
api.add_resource(ReactionCollection, "/reactions/")
api.add_resource(ThreadCollection, "/threads/")
api.add_resource(ThreadItem, "/threads/<thread:thread>/")
