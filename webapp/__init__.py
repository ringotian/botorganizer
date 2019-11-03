from flask import Flask, redirect


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('settings.py')

    @app.route('/')
    def index():
        return redirect(app.config['TELEGRAM_BOT_URL'])

    return app
