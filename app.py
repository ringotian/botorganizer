from os import environ
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from flask import Flask, request, redirect
import json
import logging
from queue import Queue
from threading import Thread
from google_auth_oauthlib.flow import Flow
import google_auth_oauthlib
from requests_oauthlib import OAuth2Session
from flask_pymongo import PyMongo
from bson import ObjectId
from flask import g
from oauthlib.oauth2 import WebApplicationClient
import requests

MONGO_URL = '{}?retryWrites=false'.format(environ.get('MONGODB_URI'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
URL = "https://{}.herokuapp.com/".format(environ.get('HEROKU_APP_NAME'))
GOOGLE_CLIENT_ID = environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")
# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)
app = Flask(__name__)
app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)
db = mongo.db

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def start(bot, context):
    text = "Привет, я бот. Вот мои args {}".format(args)
    bot.sendMessage(context.message.chat_id, text)

def help(bot, context):
    text = "HELP"
    bot.sendMessage(context.message.chat_id, text)

def message(bot, context):
    telegram_user = context.message.from_user
    text = f'Привет, пользователь {telegram_user.id}'
    bot.sendMessage(context.message.chat_id, text)

def google_auth(bot, context):
    logger.info('Пытаемся авторизоваться в гугле')
    """
    scopes = ["https://www.googleapis.com/auth/calendar"]
    client_config_data = {"web":
            {"client_id": environ.get('GOOGLE_CLIENT_ID'),
            "project_id": environ.get('GOOGLE_PROJECT_ID'),
            "auth_uri": environ.get('GOOGLE_AUTH_URI'),
            "token_uri": environ.get('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url": environ.get('GOOGLE_AUTH_URI'),
            "client_secret": environ.get('GOOGLE_CLIENT_SECRET')}}
    flow = Flow.from_client_config(
    client_config_data,
    scopes=scopes,
    redirect_uri=environ.get("GOOGLE_REDIRECT_URI"))
    auth_url, _ = flow.authorization_url(prompt='consent')
    keyboard = [[InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', 
                url = auth_url)]] 
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(context.message.chat_id, 'Авторизоваться', reply_markup=reply_markup)
    bot.sendMessage(context.message.chat_id, 'Введите код авторизации: ')
    #flow.fetch_token(code=g.google_code)
    #session = flow.authorized_session()
    
    #print(session.get('https://www.googleapis.com/userinfo/v2/me').json())
    """
    auth_url = f"https://{environ.get('HEROKU_APP_NAME')}.herokuapp.com/login/{context.message.chat_id}"
    keyboard = [[InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', 
                url = auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(context.message.chat_id, 'Авторизоваться', reply_markup=reply_markup)


 
def db_usage(bot, context):
    db_info = db.google_credentials.find_one({"_id": ObjectId('5daee3b686f95fb4a9e4f7bd')})
    if db_info:
        print("------------------------------------------------------------")
        print("GET FROM DB DATA", db_info.google_auth_code)
    else:
        logger.info("NOTHING TO PRINT")
    

def error(bot, context, error):
    logger.warn('Update "%s" caused error "%s"' % (context, error))


def main():

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('google_auth', google_auth))
    #dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_handler(CommandHandler('db_usage', db_usage))
    dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_error_handler(error)

    thread = Thread(target=dp.start, name='dp')
    thread.start()

main()

@app.route('/{}'.format(TOKEN), methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(request.get_json(force=True), bot)
        print(update)
        logger.info("Получено обновление {}".format(update.message.text))
        #dp.process_update(update)
        update_queue.put(update)
        return "OK"
    else:
        return redirect("https://t.me/testtesttesgooglecalendarbot", code=302)


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect("https://t.me/testtesttesgooglecalendarbot", code=302)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f"{URL}{TOKEN}")
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/login/<telegram_user_id>')
def login(telegram_user_id):
    g.telegram_user_id = telegram_user_id
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    print(google_provider_cfg)
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    print(authorization_endpoint)
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    print("BUILD REQUST URL")
    base_url = request.base_url.split('/')[:-1]
    base_url = '/'.join(base_url)
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=base_url + "/gCallback",
        scope=["openid", "email", "https://www.googleapis.com/auth/calendar.events"],
    )
    print(base_url)
    return redirect(request_uri)    

@app.route('/login/gCallback', methods=['GET'])
def google_callback():
   #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!") 
    #google_token = request.args['code']
    #print("GOOOGLE_TOOOOKEN: ", google_token)
    #google_credentials = db.google_credentials
    #google_auth_code = {'google_auth_code': google_token}
    #result = google_credentials.insert_one(google_auth_code)
    #google_auth_code = google_credentials.find_one({'_id': result.inserted_id})['google_auth_code']
    #print(g.google_code)

    #if google_token:
    #    return f"Скопируйте информацию и введите в бот: Your google auth code {google_auth_code}"
    #else:
    #    return 'Ошибка'

    # Get authorization code Google sent back to you
    code = request.args.get("code")
    print("CODEEEE: ", code)
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        #users_name = userinfo_response.json()["given_name"]
        print(userinfo_response.json())
        return userinfo_response.json()
    else:
        return "User email not available or not verified by Google.", 400
        
    
if __name__ == '__main__':
    app.run()
