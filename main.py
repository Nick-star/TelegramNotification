import logging
import gspread
import datetime
from time import sleep

from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Конфигурация логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger(__name__)

# Инициализация бота и Google Sheets
TOKEN = "telegram_token"
bot = Bot(token=TOKEN)
manager_chat_id = "id_of_manager"
gc = gspread.service_account(filename='credentials.json')
sheet = gc.open('name_of_sheet').sheet1


def send_reminder(context: CallbackContext):
    # Получение всех записей из Google Sheet
    records = sheet.get_all_records()
    for row in records:
        tel_id, text, date, time, answer_time = row['tel_id'], row['text'], row['date'], row['time'], row['answer_time']
        datetime_str = date + ' ' + time
        reminder_datetime = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        # Если текущее время равно времени напоминания
        if datetime.datetime.now() >= reminder_datetime:
            # Создание клавиатуры
            keyboard = [
                [
                    InlineKeyboardButton("Выполнено", callback_data='done'),
                    InlineKeyboardButton("Не сделано", callback_data='not_done'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Отправка сообщения
            context.bot.send_message(chat_id=tel_id, text=text, reply_markup=reply_markup)
            # Удаление записи из Google Sheet
            sheet.delete_row(records.index(row) + 2)
            # Установка значения answered в False для данного пользователя
            context.user_data['answered'] = False
            # Ждем ответа
            sleep(answer_time)
            if not context.user_data['answered']:
                context.bot.send_message(chat_id=manager_chat_id, text=f"Сотрудник {tel_id} проигнорировал напоминание.")


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['answered'] = True
    # Отправка сообщения менеджеру
    bot.send_message(chat_id=manager_chat_id, text=f"Сотрудник {query.message.chat.id} ответил: {query.data}")


def main():
    updater = Updater(bot=bot, use_context=True)

    dp = updater.dispatcher

    job_queue = updater.job_queue
    job_queue.run_repeating(send_reminder, interval=60, first=0, context={'answered': False})

    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
