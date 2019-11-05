from queue import Queue
from threading import Thread
from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, Filters, MessageHandler, \
                    CallbackQueryHandler
from webapp import create_app
from flask import current_app
from webapp.handlers import start, check_agenda, add_event, help, \
    google_auth, google_set_default_calendar, google_revoke, button, error

app = create_app()


def telegram_bot_runner():
    bot = Bot(current_app.config.get('TOKEN'))
    update_queue = Queue()
    dp = Dispatcher(bot, update_queue, use_context=True)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(
        Filters.regex('^(Посмотреть расписание)$'), check_agenda
        ))
    dp.add_handler(MessageHandler(
        Filters.regex('^(Создать мероприятие)$'), add_event
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


if __name__ == "__main__":
    app.run(debug=True)
    telegram_bot_runner()
