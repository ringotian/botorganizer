from flask import Flask
from flask_pymongo import PyMongo

from webapp.auth.routes import blueprint as auth_blueprint
from webapp.main.rouutes import blueprint as main_blueprint

mongo = PyMongo()


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    mongo.init_app(app)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    return app
