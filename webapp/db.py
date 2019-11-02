from flask_pymongo import PyMongo
from webapp import app


def db():
    mongo = PyMongo(app)

    return mongo
