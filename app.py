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
from bson.objectid import ObjectId

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


def print_index_table():
    return ('<table>' +
          '<tr><td><a href="/test">Test an API request</a></td>' +
          '<td>Submit an API request and see a formatted JSON response. ' +
          '    Go through the authorization flow if there are no stored ' +
          '    credentials for the user.</td></tr>' +
          '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
          '<td>Go directly to the authorization flow. If there are stored ' +
          '    credentials, you still might not be prompted to reauthorize ' +
          '    the application.</td></tr>' +
          '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
          '<td>Revoke the access token associated with the current user ' +
          '    session. After revoking credentials, if you go to the test ' +
          '    page, you should see an <code>invalid_grant</code> error.' +
          '</td></tr>' +
          '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
          '<td>Clear the access token currently stored in the user session. ' +
          '    After clearing the token, if you <a href="/test">test the ' +
          '    API request</a> again, you should go back to the auth flow.' +
          '</td></tr></table>')


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            }


def is_authorized(user_id):
    print("ID: ", user_id)
    user_str_id = str(user_id)
    print(mongo.db.google_credentials.find_one({'_id': '861969585'}))



def start(update, context):
    text = 'Привет! Что ты хочешь сделать?'
    my_keyboard = ReplyKeyboardMarkup([
                                    ['Посмотреть расписание'], ['Создать мероприятие']]
                                    )
    update.message.reply_text(text, reply_markup=my_keyboard)


def google_auth(update, context):
    auth_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/authorize/{update.message.chat_id}"
    keyboard = [
                [InlineKeyboardButton('Нажми на ссылку, чтобы авторизоваться в гугле', url=auth_url)]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Авторизоваться в google', reply_markup=reply_markup)


def help(update, context):
    text = "Чтобы начать использование бота, введите /start"
    update.message.reply_text(text)


def check_agenda(update, context):
    is_authorized(update.message.chat_id)

    # if check_user_creds is False:
    #     text = "Сначала нужно авторизоваться в гугле. \
    #         Для этого используй команду /google_auth"
    #     update.message.reply_text(text)
    # else:
    #     text = "Вот твое расписание на сегодня"
    #     update.message.reply_text(text)
    # if 'credentials' not in flask.session:
    #     return flask.redirect('authorize')

    # # Load credentials from the session.
    # credentials = google.oauth2.credentials.Credentials(
    #     **flask.session['credentials'])

    # calendar = googleapiclient.discovery.build(
    #     API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    # events_result = calendar.events().list(calendarId='primary', timeMin=now,
    #                                     maxResults=10, singleEvents=True,
    #                                     orderBy='startTime').execute()
    # print("events_result", events_result)
    # events = events_result.get('items', [])

    # if not events:
    #     print('No upcoming events found.')
    # for event in events:
    #     start = event['start'].get('dateTime', event['start'].get('date'))
    #     print(start, event['summary'])

    # # Save credentials back to session in case access token was refreshed.
    # # ACTION ITEM: In a production app, you likely want to save these
    # #              credentials in a persistent database instead.
    # #flask.session['credentials'] = credentials_to_dict(credentials)
    # #return flask.jsonify(**files)
    # return 'events'

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(
    Filters.regex('^(Посмотреть расписание)$'), check_agenda
    ))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler('google_auth', google_auth))
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
    return print_index_table()


# @app.route('/test')
# def test_api_request():
#     if 'credentials' not in flask.session:
#         return flask.redirect('authorize')

#     # Load credentials from the session.
#     credentials = google.oauth2.credentials.Credentials(
#         **flask.session['credentials'])

#     calendar = googleapiclient.discovery.build(
#         API_SERVICE_NAME, API_VERSION, credentials=credentials)

#     now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
#     print('Getting the upcoming 10 events')
#     events_result = calendar.events().list(calendarId='primary', timeMin=now,
#                                         maxResults=10, singleEvents=True,
#                                         orderBy='startTime').execute()
#     print("events_result", events_result)
#     events = events_result.get('items', [])

#     if not events:
#         print('No upcoming events found.')
#     for event in events:
#         start = event['start'].get('dateTime', event['start'].get('date'))
#         print(start, event['summary'])

#     # Save credentials back to session in case access token was refreshed.
#     # ACTION ITEM: In a production app, you likely want to save these
#     #              credentials in a persistent database instead.
#     #flask.session['credentials'] = credentials_to_dict(credentials)
#     #return flask.jsonify(**files)
#     return 'events'


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
    #mongo.google_credentials.
    #return flask.session['state']
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
            '_id': ObjectId(),
            'telegram_user_id': flask.session['user_id'],
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }
        )
    return flask.redirect(flask.url_for('index'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
        params={'token': credentials.token},
        headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.' + print_index_table())
    else:
        return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
        print_index_table())


if __name__ == '__main__':
    app.run(debug=True)
