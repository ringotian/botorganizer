from flask import Blueprint
from webapp.db import mongo

blueprint = Blueprint('auth', __name__, url_prefix='/auth')


@blueprint.route('/<userid>')
def auth(userid):
    #def_db = get_db()
    #def_db = None
    return f"Hi! I am auth func and I've got {userid} and {mongo}"


# @blueprint.route('/authorize/<userid>')
# def authorize(userid):
#     # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
#     flow = google_auth_oauthlib.flow.Flow.from_client_config(
#         settings.CLIENT_CONFIG_DATA, scopes=settings.SCOPES
#         )

#     # The URI created here must exactly match one of the authorized redirect URIs
#     # for the OAuth 2.0 client, which you configured in the API Console. If this
#     # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
#     # error.
#     flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

#     authorization_url, state = flow.authorization_url(
#     # Enable offline access so that you can refresh an access token without
#     # re-prompting the user for permission. Recommended for web server apps.
#     access_type='offline',
#     # Enable incremental authorization. Recommended as a best practice.
#     include_granted_scopes='true')

#     # Store the state so the callback can verify the auth server response.
#     flask.session['state'] = state
#     flask.session['user_id'] = userid
#     return flask.redirect(authorization_url)


# @blueprint.route('/oauth2callback')
# def oauth2callback():
#     # Specify the state when creating the flow in the callback so that it can
#     # verified in the authorization server response.
#     if 'state' in flask.session:
#         state = flask.session['state']
#         print("STATE: ", flask.session['state'])
#     flow = google_auth_oauthlib.flow.Flow.from_client_config(
#         settings.CLIENT_CONFIG_DATA, scopes=settings.SCOPES, state=state)
#     flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

#     # Use the authorization server's response to fetch the OAuth 2.0 tokens.
#     authorization_response = flask.request.url
#     flow.fetch_token(authorization_response=authorization_response)

#     # Store credentials in the session.
#     # ACTION ITEM: In a production app, you likely want to save these
#     #              credentials in a persistent database instead.
#     credentials = flow.credentials
#     #flask.session['credentials'] = credentials_to_dict(credentials)
#     #user_creds = credentials_to_dict(credentials)
#     mongo.db.google_credentials.insert_one(
#         {
#             '_id': flask.session['user_id'],
#             # 'telegram_user_id': flask.session['user_id'],
#             'token': credentials.token,
#             'refresh_token': credentials.refresh_token,
#             'token_uri': credentials.token_uri,
#             'client_id': credentials.client_id,
#             'client_secret': credentials.client_secret,
#             'scopes': credentials.scopes,
#         }
#         )
#     return flask.redirect(flask.url_for('index'))


# @blueprint.route('/clear')
# def clear_credentials():
#     if 'credentials' in flask.session:
#         del flask.session['credentials']
#     return ('Креды удалены.<br><br>')