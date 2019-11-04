from flask import Blueprint, redirect, current_app

blueprint = Blueprint('main', __name__, url_prefix='/')


@blueprint.route('/')
def index():
    return redirect(current_app.config['TELEGRAM_BOT_URL'])
