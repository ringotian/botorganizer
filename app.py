import logging
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    )
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')


def start(bot, update):
    text = 'Вызван /start'
    my_keyboard = ReplyKeyboardMarkup([['Расписание']])
    update.message.reply_text(text, reply_markup=my_keyboard)


def message(bot, update, user_data):
    user_text = "Привет {}! Ты написала: {}".format(
                update.message.chat.first_name, update.message.text
                )
    update.message.reply_text(user_text)


def main():
    mybot = Updater()
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, message))

    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
