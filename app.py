from os import environ
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import json
import logging
from queue import Queue
from threading import Thread

MONGO_URL = '{}?retryWrites=false'.format(environ.get('MONGODB_URI'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOKEN = environ.get('TELEGRAM_BOT_TOKEN')

bot = Bot(TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)


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
 
if __name__ == '__main__':
    main()
