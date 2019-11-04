from flask_pymongo import PyMongo


mongo = PyMongo()


def get_db():
    return mongo.db['google_credentials']
