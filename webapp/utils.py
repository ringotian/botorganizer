import google.oauth2.credentials
import googleapiclient.discovery
from webapp.db import mongo
from flask import current_app


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


def build_google_api_obj(id=update.message.chat_id):
    user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(id)}
            )
    user_credentials_dict = credentials_to_dict(user_credentials_from_db)
    credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
    calendar = googleapiclient.discovery.build(
            current_app.config.get('API_SERVICE_NAME'),
            current_app.config.get('API_VERSION'),
            credentials=credentials)
    return calendar


def get_default_calendar_from_db(id=update.message.chat_id):
    user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(id)}
            )
    default_calendar_id = user_credentials_from_db['default_calendar']
    return default_calendar_id
