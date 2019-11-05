from flask import Flask
from webapp.auth.routes import blueprint as auth_blueprint
from webapp.main.routes import blueprint as main_blueprint
from webapp.db import mongo
from webapp.bot_organizer import telegram_bot_runner


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    mongo.init_app(app)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    telegram_bot_runner()
    return app
