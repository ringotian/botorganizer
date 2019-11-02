from flask import Flask, redirect
from webapp import blueprint as auth_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('settings.py')
    app.config['MONGO_URI'] = app.config['MONGODB_URI']+'?retryWrites=false'
    app.register_blueprint(auth_blueprint)

    @app.route('/')
    def index():
        return redirect(app.config['TELEGRAM_BOT_URL'])

    return app
