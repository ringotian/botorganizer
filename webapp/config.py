from os import environ

TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = environ.get('TELEGRAM_BOT_URL')
URL = "https://{}.herokuapp.com/".format(environ.get('HEROKU_APP_NAME'))
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
CLIENT_CONFIG_DATA = {
    "web":
        {
            "client_id": environ.get('GOOGLE_CLIENT_ID'),
            "project_id": environ.get('GOOGLE_PROJECT_ID'),
            "auth_uri": environ.get('GOOGLE_AUTH_URI'),
            "token_uri": environ.get('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url":
            environ.get('GOOGLE_AUTH_CERT_URI'),
            "client_secret": environ.get('GOOGLE_CLIENT_SECRET')}
        }
HEROKU_APP_NAME = environ.get('HEROKU_APP_NAME')
MONGO_URI = environ.get('MONGODB_URI')+'?retryWrites=false'
MONGO_AUTH_COLLECTION = 'google_credentials'
FLASK_SESSION_KEY = environ.get('FLASK_SESSION_KEY')
