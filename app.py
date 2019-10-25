import logging
import os
import requests
from queue import Queue
from threading import Thread
from telegram import Bot, Update, ReplyKeyboardMarkup, InlineKeyboardButton, \
                    InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, \
                        RegexHandler
from flask import Flask, redirect, request, session, jsonify, url_for
#from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
logger = logging.getLogger(__name__)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = os.environ.get('TELEGRAM_BOT_URL')
URL = "https://{}.herokuapp.com/".format(os.environ.get('HEROKU_APP_NAME'))
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
client_config_data = {
         "web": {
                 "client_id": os.environ.get('DRIVE_CLIENT_ID'),
                 "project_id": os.environ.get('DRIVE_PROJECT_ID'),
                 "auth_uri": os.environ.get('DRIVE_AUTH_URI'),
                 "token_uri": os.environ.get('DRIVE_TOKEN_URI'),
                 "auth_provider_x509_cert_url": os.environ.get('DRIVE_AUTH_CERT'),
                 "client_secret": os.environ.get('DRIVE_CLIENT_SECRET')}}

app = Flask(__name__)
logger.info("START")


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
#     return flow


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


# flow = google_auth_flow()
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
        return redirect("https://t.me/life_organizer_bot", code=302)


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(TELEGRAM_BOT_URL, code=302)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f"{URL}{TOKEN}")
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


# @app.route('/auth', methods=['GET', 'POST'])
# def auth():
#     auth_url, _ = flow.authorization_url(prompt='consent')
#     return redirect(auth_url)


# @app.route('/login/gcallback', methods=['GET', 'POST'])
# def gcallback():
#     google_auth_code = request.args.get("code")
#     flow.fetch_token(code=google_auth_code)
#     session = flow.authorized_session()
#     print(session.get('https://www.googleapis.com/userinfo/v2/me').json())
#     return "ok"


@app.route('/test')
def test_api_request():
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
            **session['credentials'])

    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    files = drive.files().list().execute()
    #   Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    session['credentials'] = credentials_to_dict(credentials)
    return jsonify(**files)


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
         client_config_data,
         scopes=SCOPES,
         redirect_uri=os.environ.get("DRIVE_REDIRECT_URI"))

    # The URI created here must exactly match one of the authorized redirect URIs   
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
         client_config_data,
         scopes=SCOPES,
         redirect_uri=os.environ.get("DRIVE_REDIRECT_URI"),
         state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('test_api_request'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return ('You need to <a href="/authorize">authorize</a> before ' + 'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
                    **session['credentials'])

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
    if 'credentials' in session:
        del session['credentials']
        return ('Credentials have been cleared.<br><br>' + print_index_table())


if __name__ == "__main__":
    app.run()
