import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

        # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    from src.models import init_db, populate_db
    from src.resources.user import UserConverter
    from src.resources.thread import ThreadConverter
    from src.resources.Message import MessageConverter
    from . import api
    app.cli.add_command(init_db)
    app.cli.add_command(populate_db)
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["thread"] = ThreadConverter
    app.url_map.converters["message"] = MessageConverter
    app.register_blueprint(api.api_bp)

    return app
