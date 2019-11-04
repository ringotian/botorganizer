from flask import Flask, redirect
from flask_pymongo import PyMongo

from webapp.auth.routes import blueprint as auth_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('settings.py')
    app.config['MONGO_URI'] = app.config['MONGODB_URI']+'?retryWrites=false'
    mongo = PyMongo(app)
    mongo.init_app(app)
    app.register_blueprint(auth_blueprint)

    @app.route('/')
    def index():
        return redirect(app.config['TELEGRAM_BOT_URL'])

    return app
