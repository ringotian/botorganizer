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
from telegram.ext import Dispatcher, CommandHandler, RegexHandler
import oauth2client

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
CLIENT_SECRETS_FILE = "client_secret.json"
app = flask.Flask(__name__)
app.secret_key = os.environ.get('FLASK_SESSION_KEY')
bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)


def credentials_to_dict(credentials):
    return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


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


@app.route('/test')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    calendar = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = calendar.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)
    #return flask.jsonify(**files)
    return 'events'


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG_DATA, scopes=SCOPES)

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
    print("WOW STATE IS HERE: ", state)
    flask.session['state'] = state
    print("AND FROM FLASK SESSION: ", flask.session['state'])

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
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('test_api_request'))


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
