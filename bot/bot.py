import telebot
from telebot import types
import requests
from dotenv import dotenv_values
from threading import Thread

from db import create_user, get_all_users, get_user_by_username, delete_user
from pooling import poolingStatus

config = dotenv_values(".env")
bot = telebot.TeleBot(config.get("BOT_TOKEN"))
bot.delete_my_commands()

GET_STATUS = "Що по світлу?"
SUBSCRIBE = "Отримувати статуси"
UNSUBSCRIBE = "Відписатись"

greating = """
    Вітаю! 
Я можу дізнаватись для вас чи є світло в домі.

А ще я можу відправляти вам повідомлення коли світло зʼявляється чи зникає.
"""

THANKS_FOR_SUBSCRIPTION = "Дякую що підписалися"

YOU_HAVE_SUBSCRIBED = "Ви вже підписані"

UNSIBSCRIBE_MESSAGE = "Ми відписали вас. Ви більше не будете отримувати сповіщення"


def get_markup(chat_id):
    subscription = get_user_by_username(chat_id)

    first_button = types.KeyboardButton(GET_STATUS)

    if subscription is None:
        second_button = types.KeyboardButton(SUBSCRIBE)
    else:
        second_button = types.KeyboardButton(UNSUBSCRIBE)

    markup = types.ReplyKeyboardMarkup()
    markup.row(first_button, second_button)

    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id

    bot.reply_to(message, greating, reply_markup=get_markup(chat_id))


@bot.message_handler(commands=['options'])
def send_options(message):
    markup = types.InlineKeyboardMarkup()
    button_a = types.InlineKeyboardButton('Option A', callback_data='A')
    button_b = types.InlineKeyboardButton('Option B', callback_data='B')
    markup.add(button_a, button_b)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == 'A':
        bot.answer_callback_query(call.id, "You chose Option A")
    elif call.data == 'B':
        bot.answer_callback_query(call.id, "You chose Option B")


@bot.message_handler(func=lambda message: message.text == GET_STATUS)
def get_status(message):
    response = requests.get(config.get("GET_STATUS_ENDPOINT"))

    if response.status_code == 200:
        bot.reply_to(message, "💡💡💡 Світло є!")
    else:
        bot.reply_to(message, "🔦 Світла немає. Готуйте ліхтарик.")


@bot.message_handler(func=lambda message: message.text == SUBSCRIBE)
def subscribe(message):
    chat_id = message.chat.id
    username = message.from_user.username

    subscription = get_user_by_username(chat_id)

    if subscription is None:
        print(subscription)
        create_user(chat_id, username)
        bot.send_message(chat_id, THANKS_FOR_SUBSCRIPTION, reply_markup=get_markup(chat_id))
    else:
        bot.send_message(chat_id, YOU_HAVE_SUBSCRIBED, reply_markup=get_markup(chat_id))


@bot.message_handler(func=lambda message: message.text == UNSUBSCRIBE)
def unsubscribe(message):
    chat_id = message.chat.id

    if delete_user(chat_id):
        bot.send_message(chat_id, UNSIBSCRIBE_MESSAGE, reply_markup=get_markup(chat_id))
    else:
        bot.send_message(chat_id, "Щось пішло не так", reply_markup=get_markup(chat_id))


def notify(hasElectricuty):
    if hasElectricuty is True:
        message = "Світло!"
    else:
        message = "Світло все :("

    subscribed_users = get_all_users()

    for user in subscribed_users:
        bot.send_message(user, message)


# Start the bot polling in a separate thread
def start_bot():
    bot.polling()


if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    poolingStatus(config.get("GET_STATUS_ENDPOINT"), notify)
