from os import environ
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import logging
from queue import Queue
from threading import Thread
from flask import Flask, request, redirect

logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
URL = "https://{}.herokuapp.com/".format(environ.get('HEROKU_APP_NAME'))
logger.info(TOKEN)
bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)
app = Flask(__name__)


def start(bot, context):
    keyboard = [
        ['Расписание'], ['Добавить задачу в trello'], ['Заметки']
    ]
    main_menu_keyboard = ReplyKeyboardMarkup(keyboard)
    bot.sendMessage(context.message.chat_id, reply_markup=main_menu_keyboard)


def help(bot, context):
    text = "Чтобы запустить бота, нажмите /start"
    bot.sendMessage(context.message.chat_id, text)


def message(bot, context):
    telegram_user = context.message.from_user
    text = f'Привет, пользователь {telegram_user.id}'
    bot.sendMessage(context.message.chat_id, text)


def error(bot, context, error):
    logger.warn('Update "%s" caused error "%s"' % (context, error))


def main():
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_error_handler(error)
    thread = Thread(target=dp.start, name='dp')
    thread.start()


main()


@app.route('/{}'.format(TOKEN), methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(request.get_json(force=True), bot)
        logger.info("Получено обновление {}".format(update.message.text))
        update_queue.put(update)
        return "OK"
    else:
        return redirect("https://t.me/life_organizer_bot", code=302)


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect("https://t.me/life_organizer_bot", code=302)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f"{URL}{TOKEN}")
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


if __name__ == '__main__':
    app.run()
