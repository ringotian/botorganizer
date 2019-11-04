from app import mongo


def get_db():
    return mongo.db['google_credentials']
