import logging
import os
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, \
                    InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from flask import Flask, redirect
from google_auth_oauthlib.flow import Flow

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = os.environ.get('TELEGRAM_BOT_URL')
app = Flask(__name__)


def start(bot, update):
    my_keyboard = ReplyKeyboardMarkup([
                                    ['Расписание'], ['Создать мероприятие']]
                                    )
    update.message.reply_text(reply_markup=my_keyboard)


def google_auth(bot, update):
    auth_url = f"https://{environ.get('HEROKU_APP_NAME')}.herokuapp.com/login/"
    keyboard = [
                [InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', url=auth_url)]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Авторизоваться в google', reply_markup=reply_markup)


def help(bot, update):
    text = "HELP"
    update.message.reply_text(text)


def message(bot, update):
    user_text = "Привет {}! Ты написала: {}".format(
                update.message.chat.first_name, update.message.text
                )
    update.message.reply_text(user_text)

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

def main():
    mybot = Updater(TOKEN)
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('google_auth', google_auth))
    dp.add_handler(MessageHandler(Filters.text, message))

    mybot.start_polling()
    mybot.idle()


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


if __name__ == "__main__":
    main()
    app.run()
