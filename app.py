import logging
import os
from queue import Queue
from threading import Thread
from telegram import Bot, Update, ReplyKeyboardMarkup, InlineKeyboardButton, \
                    InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, \
                        RegexHandler
from flask import Flask, redirect, request
from google_auth_oauthlib.flow import Flow

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
logger = logging.getLogger(__name__)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = os.environ.get('TELEGRAM_BOT_URL')
URL = "https://{}.herokuapp.com/".format(os.environ.get('HEROKU_APP_NAME'))
app = Flask(__name__)
logger.info("START")


def start(bot, update):
    text = 'Привет! Что ты хочешь сделать?'
    my_keyboard = ReplyKeyboardMarkup([
                                    ['Посмотреть расписание'], ['Создать мероприятие']]
                                    )
    update.message.reply_text(text, reply_markup=my_keyboard)


def google_auth(bot, update):
    auth_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/login/"
    keyboard = [
                [InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', url=auth_url)]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Авторизоваться в google', reply_markup=reply_markup)


def help(bot, update):
    text = "HELP"
    update.message.reply_text(text)


def check_agenda(bot, update, user_data):
    text = "Вот твое расписание на сегодня"
    update.message.reply_text(text)


def message(bot, update):
    user_text = "Привет {}! Ты написала: {}".format(
                update.message.chat.first_name, update.message.text
                )
    update.message.reply_text(user_text)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


# def google_auth_flow():
#     scopes = ["https://www.googleapis.com/auth/calendar"]
#     client_config_data = {
#         "web": {
#                 "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
#                 "project_id": os.environ.get('GOOGLE_PROJECT_ID'),
#                 "auth_uri": os.environ.get('GOOGLE_AUTH_URI'),
#                 "token_uri": os.environ.get('GOOGLE_TOKEN_URI'),
#                 "auth_provider_x509_cert_url": os.environ.get('GOOGLE_AUTH_CERT_URI'),
#                 "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET')}}
#     flow = Flow.from_client_config(
#         client_config_data,
#         scopes=scopes,
#         redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI"))   


#def setup_bot(token=TOKEN):
bot = Bot(TOKEN)
update_queue = Queue()

dp = Dispatcher(bot, update_queue)

dp.add_handler(CommandHandler("start", start))
dp.add_handler(
                RegexHandler('^(Посмотреть расписание)$', 
                check_agenda, 
                pass_user_data=True)
            )
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler('google_auth', google_auth))
dp.add_handler(MessageHandler(Filters.text, message))
dp.add_error_handler(error)

thread = Thread(target=dp.start, name='dp')
thread.start()

    #return update_queue


#bot_update_queue = setup_bot(TOKEN)


@app.route('/{}'.format(TOKEN), methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(request.get_json(force=True), bot)
        print(update)
        logger.info("Получено обновление {}".format(update.message.text))
        update_queue.put(update)
        return "OK"
    else:
        return redirect("https://t.me/testtesttesgooglecalendarbot", code=302)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f"{URL}{TOKEN}")
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(TELEGRAM_BOT_URL, code=302)


@app.route('/login')
def login():
    scopes = ["https://www.googleapis.com/auth/calendar"]
    client_config_data = {
        "web": {
                "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
                "project_id": os.environ.get('GOOGLE_PROJECT_ID'),
                "auth_uri": os.environ.get('GOOGLE_AUTH_URI'),
                "token_uri": os.environ.get('GOOGLE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.environ.get('GOOGLE_AUTH_CERT_URI'),
                "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET')}}
    flow = Flow.from_client_config(
        client_config_data,
        scopes=scopes,
        redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI"))
    auth_url, _ = flow.authorization_url(prompt='consent')
    google_code = input('Введите код авторизации: ')
    flow.fetch_token(code=google_code)
    session = flow.authorized_session()
    print(session.get('https://www.googleapis.com/userinfo/v2/me').json())
    return "We has been here"


if __name__ == "__main__":
    app.run()
