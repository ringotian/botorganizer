from flask import Blueprint, redirect, current_app, request, g
from telegram import Update
blueprint = Blueprint('main', __name__, url_prefix='/')


@blueprint.route('/')
def index():
    return redirect(current_app.config['TELEGRAM_BOT_URL'])


@blueprint.route('/{}'.format(current_app.config.get('TOKEN')), methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(request.get_json(force=True), g.bot)
        g.update_queue.put(update)
        return "OK"
