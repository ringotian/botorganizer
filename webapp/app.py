import os
import flask
import datetime
import google_auth_oauthlib.flow
import logging
from queue import Queue
from threading import Thread
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, Filters, MessageHandler, \
                    CallbackQueryHandler, JobQueue
from flask_pymongo import PyMongo
import settings


logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    )
logger = logging.getLogger(__name__)

# app = flask.Flask(__name__)
# app.config['MONGO_URI'] = os.environ.get('MONGODB_URI')+'?retryWrites=false'
# mongo = PyMongo(app)
google_credentials = mongo.db['google_credentials']
app.secret_key = os.environ.get('FLASK_SESSION_KEY')
bot = Bot(settings.TOKEN)
update_queue = Queue()
job = JobQueue(bot)
dp = Dispatcher(bot, update_queue, job_queue=job, use_context=True)


def callback_alarm(context):
    logger.info("BEEEEEEEP!!!!!")
    print(context.job.context)
    context.bot.send_message(chat_id=context.job.context, text='BEEP')


def tomato_start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Setting a timer for 1 minute!')

    print("Where is my context? {}".format(datetime.datetime.now()), context.job_queue.__dir__)
    context.job_queue.run_once(
        callback_alarm, 5, context=update.message.chat_id
        )


def hi_user(context):
    print(context.job.context)
    print("TEST")
    #context.bot.send_message(chat_id=context.job.context, text='Hi!')


dp.job_queue.run_repeating(hi_user, interval=5)


# def callback_timer(update, context):
#     context.bot.send_message(chat_id=update.message.chat_id,
#                              text='Setting a timer for 1 minute!')

#     context.job_queue.run_once(callback_alarm, 60, context=update.message.chat_id)


dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(
    Filters.regex('^(Посмотреть расписание)$'), check_agenda
    ))
dp.add_handler(MessageHandler(
    Filters.regex('^(Создать мероприятие)$'), add_event
    ))
dp.add_handler(MessageHandler(
    Filters.regex('^(Запустить помидорки)$'), tomato_start
    ))
dp.add_handler(CommandHandler("help", help))
dp.add_handler(CommandHandler('google_auth', google_auth))
dp.add_handler(CommandHandler(
    'google_set_default_calendar', google_set_default_calendar)
    )
dp.add_handler(CallbackQueryHandler(button))
dp.add_handler(CommandHandler('google_revoke', google_revoke))
dp.add_error_handler(error)

thread = Thread(target=dp.start, name='dp')
thread.start()


@app.route('/{}'.format(settings.TOKEN), methods=['GET', 'POST'])
def webhook():
    if flask.request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(flask.request.get_json(force=True), bot)
        update_queue.put(update)
        return "OK"





if __name__ == '__main__':
    app.run()
