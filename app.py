import os
import flask
import requests
import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import logging
from queue import Queue
from threading import Thread
from telegram import Bot, Update, ReplyKeyboardMarkup, InlineKeyboardButton, \
                    InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, \
                        RegexHandler

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
logger = logging.getLogger(__name__)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = os.environ.get('TELEGRAM_BOT_URL')
URL = "https://{}.herokuapp.com/".format(os.environ.get('HEROKU_APP_NAME'))
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
CLIENT_CONFIG_DATA = {
    "web":
        {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "project_id": os.environ.get('GOOGLE_PROJECT_ID'),
            "auth_uri": os.environ.get('GOOGLE_AUTH_URI'),
            "token_uri": os.environ.get('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.environ.get('GOOGLE_AUTH_CERT_URI'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET')}
        }
app = flask.Flask(__name__)
app.secret_key = os.environ.get('FLASK_SESSION_KEY')
bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)


def start(bot, update):
    text = 'Привет! Что ты хочешь сделать?'
    my_keyboard = ReplyKeyboardMarkup([
                                    ['Посмотреть расписание'], ['Создать мероприятие']]
                                    )
    update.message.reply_text(text, reply_markup=my_keyboard)


def google_auth(bot, update):
    auth_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/auth"
    keyboard = [
                [InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', url=auth_url)]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Авторизоваться в google', reply_markup=reply_markup)


def help(bot, update):
    text = "Чтобы начать использование бота, введите /start"
    update.message.reply_text(text)


def check_agenda(bot, update, user_data):
    text = "Вот твое расписание на сегодня"
    update.message.reply_text(text)


# def message(bot, update):
#     user_text = "Привет {}! Ты написала: {}".format(
#                 update.message.chat.first_name, update.message.text
#                 )
#     update.message.reply_text(user_text)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


dp.add_handler(CommandHandler("start", start))
dp.add_handler(
                RegexHandler('^(Посмотреть расписание)$', 
                check_agenda, 
                pass_user_data=True)
            )
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler('google_auth', google_auth))
# dp.add_handler(MessageHandler(Filters.text, message))
dp.add_error_handler(error)

thread = Thread(target=dp.start, name='dp')
thread.start()


@app.route('/{}'.format(TOKEN), methods=['GET', 'POST'])
def webhook():
    if flask.request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(flask.request.get_json(force=True), bot)
        logger.info("Получено обновление {}".format(update.message.text))
        update_queue.put(update)
        return "OK"


if __name__ == '__main__':
    app.run(debug=True)
