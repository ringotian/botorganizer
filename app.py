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
from telegram.ext import Dispatcher, CommandHandler, Filters, MessageHandler
from flask_pymongo import PyMongo
import pprint

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
            "auth_provider_x509_cert_url":
            os.environ.get('GOOGLE_AUTH_CERT_URI'),
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET')}
        }
CLIENT_SECRETS_FILE = "client_secret.json"
app = flask.Flask(__name__)
app.config['MONGO_URI'] = os.environ.get('MONGODB_URI')+'?retryWrites=false'
mongo = PyMongo(app)
google_credentials = mongo.db['google_credentials']
app.secret_key = os.environ.get('FLASK_SESSION_KEY')
bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue, use_context=True)


def credentials_to_dict(credentials):
    return {'token': credentials['token'],
            'refresh_token': credentials['refresh_token'],
            'token_uri': credentials['token_uri'],
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'scopes': credentials['scopes'],
            }


def is_authorized(user_id):
    user_str_id = str(user_id)
    result = mongo.db.google_credentials.find_one({'_id': user_str_id})
    if result is not None:
        return True
    else:
        return False


def start(update, context):
    text = 'Привет! Что ты хочешь сделать?'
    my_keyboard = ReplyKeyboardMarkup([
                                    ['Посмотреть расписание'], ['Создать мероприятие']]
                                    )
    update.message.reply_text(text, reply_markup=my_keyboard)


def google_auth(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is True:
        text = "Ты уже авторизована. Если хочешь отозвать авторизацию, \
            используй /google_revoke"
        update.message.reply_text(text)
    else:
        auth_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/authorize/{update.message.chat_id}"
        keyboard = [
                    [InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', url=auth_url)]
                    ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Авторизоваться в google', reply_markup=reply_markup)


def help(update, context):
    text = """
    Чтобы начать использование бота, введи /start
    Чтобы пройти выторизацию в гугле, используй /google_auth
    Чтобы отозвать разрешение на использование гугл аккаунта, используй /google_revoke.
    Чтобы выбрать календарь по умолчанию, используй /google_set_default_calendar"""
    update.message.reply_text(text)


def google_revoke(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Ты не авторизована. Если хочешь пройти авторизацию, \
            используй /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
                    params={'token': credentials.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'})
        status_code = getattr(revoke, 'status_code')
        if status_code == 200:
            mongo.db.google_credentials.find_one_and_delete(
                    {'_id': str(update.message.chat_id)}
                )
            text = 'Разрешение на доступ к календарю отозвано'
            update.message.reply_text(text)
        else:
            text = 'Произошла ошибка, пожалуйста, напишите на почту lad.shada@gmail.com'
            update.message.reply_text(text)


def check_agenda(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле. \
            Для этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        calendar = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = calendar.events().list(
                                        calendarId='primary',
                                        timeMin=now,
                                        maxResults=10,
                                        singleEvents=True,
                                        orderBy='startTime').execute()
        events = events_result.get('items', [])
        text = ''
        if not events:
            text = 'У вас нет предстоящих событий в календаре'
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            text = text + start + ' ' + event['summary'] + '\n'
        update.message.reply_text(text)


def add_event(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле. \
            Для этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        calendar = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        # Create data for event
        current_date = datetime.datetime.now().date()
        tomorrow = datetime.datetime(current_date.year, current_date.month, current_date.day, 10) + datetime.timedelta(days=1)
        event_start = tomorrow.isoformat()
        event_end = (tomorrow + datetime.timedelta(hours=1)).isoformat()

        event_result = calendar.events().insert(calendarId='primary',
                        body={
                            "summary": 'Test event created by telegram bot',
                            "description": "This is the test event",
                            "start": {"dateTime": event_start, "timeZone": 'GMT+03:00'},
                            "end": {"dateTime": event_end, "timeZone": 'GMT+03:00'},
                        }).execute()
        print("created event")
        print("id: ", event_result['id'])
        print("summary: ", event_result['summary'])
        print("starts at: ", event_result['start']['dateTime'])
        print("ends at: ", event_result['end']['dateTime'])
        update.message.reply_text('Событие создано')


def google_set_default_calendar(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле. \
            Для этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        calendar = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)
        calendars = calendar.calendarList().list().execute()
        for calendar in calendars:
            pprint.pprint(calendar['items'])
        #update.message.reply_text(calendars)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(
    Filters.regex('^(Посмотреть расписание)$'), check_agenda
    ))
dp.add_handler(MessageHandler(
    Filters.regex('^(Создать мероприятие)$'), add_event
    ))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler('google_auth', google_auth))
dp.add_handler(CommandHandler('google_set_default_calendar', google_set_default_calendar))
dp.add_handler(CommandHandler('google_revoke', google_revoke))
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


@app.route('/')
def index():
    return flask.redirect(TELEGRAM_BOT_URL)


@app.route('/authorize/<userid>')
def authorize(userid):
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG_DATA, scopes=SCOPES
        )

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    flask.session['user_id'] = userid
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    if 'state' in flask.session:
        state = flask.session['state']
        print("STATE: ", flask.session['state'])
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG_DATA, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    #flask.session['credentials'] = credentials_to_dict(credentials)
    #user_creds = credentials_to_dict(credentials)
    mongo.db.google_credentials.insert_one(
        {
            '_id': flask.session['user_id'],
            # 'telegram_user_id': flask.session['user_id'],
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }
        )
    return flask.redirect(flask.url_for('index'))


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Креды удалены.<br><br>')


if __name__ == '__main__':
    app.run(debug=True)
