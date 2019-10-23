import logging
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from flask import Flask, redirect

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_URL = os.environ.get('TELEGRAM_BOT_URL')
app = Flask(__name__)


def start(bot, update):
    text = 'Вызван /start'
    my_keyboard = ReplyKeyboardMarkup([['Расписание']])
    update.message.reply_text(text, reply_markup=my_keyboard)


def help(bot, update):
    text = "HELP"
    update.message.reply_text(text)


def message(bot, update):
    user_text = "Привет {}! Ты написала: {}".format(
                update.message.chat.first_name, update.message.text
                )
    update.message.reply_text(user_text)


def main():
    mybot = Updater(TOKEN)
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, message))

    mybot.start_polling()
    mybot.idle()


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(TELEGRAM_BOT_URL, code=302)


if __name__ == "__main__":
    main()
    app.run()
