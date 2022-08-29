import requests
import os
from http import HTTPStatus
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
from datetime import date, timedelta
from dotenv import load_dotenv
import logging
# from logging.handlers import RotatingFileHandler

load_dotenv()

# настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    filemode='w',
    format=('%(asctime)s, %(levelname)s, %(name)s, %(message)s,' +
            '%(funcName)s, %(lineno)d')
)

URL = 'http://api.football-data.org/v4/competitions/'
TOKEN = os.getenv('FOOTBALL_DATA_TOKEN')
TELE_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
if not TOKEN or not TELE_TOKEN or not CHAT_ID:
    logging.error('отсутствует переменная окружения ')
countries = {'Англия': 2021, 'Лига Чемпионов': 2001, 'Франция': 2015,
             'Германия': 2002, 'Италия': 2019, 'Испания': 2014}


# def create_logger():
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.INFO)
#     handler = RotatingFileHandler(
#         'main.log', maxBytes=50000000, backupCount=5
#     )
#     logger.addHandler(handler)
#     formatter = logging.Formatter(
#         '%(asctime)s, %(levelname)s, %(name)s, %(message)s'
#     )
#     handler.setFormatter(formatter)
#     return logger


def get_match_info(champ_id):
    ''' получаем полную инфу о матчах за 3 дня '''
    filters = {'dateFrom': date.today() - timedelta(days=1),
               'dateTo': date.today() + timedelta(days=1),
               'season': 2022}
    headers = {'X-Auth-Token': TOKEN}
    url = f'{URL}{champ_id}/matches/'
    matches = {}
    try:
        matches = requests.get(
            url, params=filters, headers=headers
        )
        if matches.status_code != HTTPStatus.OK:
            logging.error(
                'ошибка доступа к данным по матчам ' + str(matches.status_code)
            )
        else:
            matches = matches.json()
    except Exception as error:
        logging.error('ошибка доступа к данным по матчам ' + str(error))
    return matches


def get_results(chat_id, champ_id):
    ''' парсим словарь в нужную форму '''
    matches = get_match_info(champ_id)
    text = []
    try:
        for match in matches['matches']:
            line = (f'Тур {match["matchday"]}. {match["homeTeam"]["name"]} ' +
                    f'{match["score"]["fullTime"]["home"]} - ' +
                    f'{match["score"]["fullTime"]["away"]} ' +
                    f'{match["awayTeam"]["name"]} {match["status"]}')
            text.append(line)
    except Exception as error:
        try:
            bot.send_message(chat_id, str(error))
        except Exception as bot_error:
            logging.error('ошибка бота ' + str(bot_error))
        logging.error('пришел пустой словарь ' + str(error))
    return text


def say_hi(update, context):
    ''' Ответ на текстовое сообщение пользователя '''
    # Получаем информацию о чате, из которого пришло сообщение,
    # и сохраняем в переменную chat
    chat = update.effective_chat
    # получаем текст сообщения для нужной реакции
    text = update.message['text']
    if text in countries:
        champ_id = countries[text]
        text_lines = get_results(chat.id, champ_id)
        text = '\n'.join(text_lines)
        try:
            context.bot.send_message(chat_id=chat.id, text=text)
        except Exception as bot_error:
            logging.error('ошибка бота ' + str(bot_error))
    else:
        try:
            context.bot.send_message(
                chat_id=chat.id, text='Некорректный чемпионат'
            )
        except Exception as bot_error:
            logging.error('ошибка бота ' + str(bot_error))
        logging.debug('некорректное имя чемпионата' + text)


def wake_up(update, context):
    ''' обработка команды запуска бота '''
    # update содержит информацию о чате и сообщении в формате словаря,
    # ключи через точку
    chat = update.effective_chat
    buttons = ReplyKeyboardMarkup([['Англия', 'Испания'],
                                  ['Германия', 'Франция'],
                                  ['Италия', 'Лига Чемпионов']],
                                  resize_keyboard=True)
    try:
        context.bot.send_message(
            chat_id=chat.id, text='Древнее зло пробудилось!',
            reply_markup=buttons
        )
    except Exception as bot_error:
        logging.error('ошибка бота ' + str(bot_error))


if __name__ == '__main__':
    try:
        bot = Bot(token=TELE_TOKEN)
        updater = Updater(token=TELE_TOKEN)
        # обработчик команд должен идти выше обработчика сообщений,
        # поскольку команда - тоже сообщение
        # обрабатывает команду /command из чата
        updater.dispatcher.add_handler(CommandHandler('start', wake_up))
        # Filters.photo, Filters.video, Filters.all
        updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi))
        updater.start_polling(poll_interval=20)
    except Exception as bot_error:
        logging.error('ошибка бота ' + str(bot_error))
