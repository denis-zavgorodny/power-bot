import telebot
from telebot import types
import requests
from dotenv import dotenv_values
from threading import Thread

from db import subscribe, get_all_subscribers, get_subscriber, unsubscribe
from logger import get_logger

from pooling import pooling_status
from text_messages import GREATING_TEXT, ELECTRICITY_OK, ELECTRICITY_FAIL, ELECTRICITY_UNKNOWN, THANKS_FOR_SUBSCRIPTION, \
    YOU_HAVE_SUBSCRIBED, SUBSCRIPTION_WITH_ERROR, UNSIBSCRIBE_MESSAGE, UNSIBSCRIBE_MESSAGE_NO_USER, ELECTRICITY_BACK, \
    ELECTRICITY_GONE

logger = get_logger()

config = dotenv_values(".env")
bot = telebot.TeleBot(config.get("BOT_TOKEN"))
# bot.delete_my_commands()

GET_STATUS_BUTTON = {"text": "Що по світлу?", "code": "1"}
SUBSCRIBE_BUTTON = {"text": "Підписатись", "code": "2"}
UNSUBSCRIBE_BUTTON = {"text": "Відписатись", "code": "3"}


def get_markup(chat_id):
    # subscription = get_subscriber(chat_id)

    first_button = types.InlineKeyboardButton(text=GET_STATUS_BUTTON["text"], callback_data=GET_STATUS_BUTTON["code"])

    # if subscription is None:
    #     second_button = types.InlineKeyboardButton(text=SUBSCRIBE_BUTTON["text"], callback_data=SUBSCRIBE_BUTTON["code"])
    # else:
    #     second_button = types.InlineKeyboardButton(text=UNSUBSCRIBE_BUTTON["text"], callback_data=UNSUBSCRIBE_BUTTON["code"])

    markup = types.InlineKeyboardMarkup()
    markup.row(first_button)

    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id

    bot.reply_to(message, GREATING_TEXT, reply_markup=get_markup(chat_id))


@bot.message_handler(commands=['menu'])
def send_menu(message):
    chat_id = message.chat.id

    bot.reply_to(message, "Чим я можу допомогти?", reply_markup=get_markup(chat_id))


@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, get_status())


@bot.message_handler(commands=['subscribe'])
def send_subscribe(message):
    bot.reply_to(message, subscribe_user(message))


@bot.message_handler(commands=['unsubscribe'])
def send_unsubscribe(message):
    bot.reply_to(message, unsubscribe_user(message))


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == GET_STATUS_BUTTON["code"]:
        bot.send_message(call.message.chat.id, get_status())
    elif call.data == SUBSCRIBE_BUTTON["code"]:
        text = subscribe_user(call.message)
        bot.send_message(call.message.chat.id, text)
    elif call.data == UNSUBSCRIBE_BUTTON["code"]:
        text = unsubscribe_user(call.message)
        bot.send_message(call.message.chat.id, text)

    bot.answer_callback_query(call.id)  # Acknowledge the callback query

@bot.message_handler(commands=['ping'])
def send_welcome(message):
    notify(False)


def get_status():
    try:
        response = requests.get(config.get("GET_STATUS_ENDPOINT"))
        res = response.json()

        if res["has_electricity"] is True:
            return ELECTRICITY_OK.format(res["message"])
        else:
            return ELECTRICITY_FAIL.format(res["message"])
    except requests.exceptions.RequestException as e:
        logger.error(f"Get status request failed: {e}")
        return ELECTRICITY_UNKNOWN


def subscribe_user(message):
    chat_id = message.chat.id
    try:
        chat_id = message.chat.id
        username = message.from_user.username

        subscription = get_subscriber(chat_id)

        if subscription is None:
            subscribe(chat_id, username)
            return THANKS_FOR_SUBSCRIPTION
        else:
            return YOU_HAVE_SUBSCRIBED
    except Exception as e:
        logger.error(f"Subscribe request failed for chat_id #{chat_id}: {e}")
        return SUBSCRIPTION_WITH_ERROR


def unsubscribe_user(message):
    chat_id = message.chat.id

    try:
        if unsubscribe(chat_id):
            return UNSIBSCRIBE_MESSAGE
        else:
            return UNSIBSCRIBE_MESSAGE_NO_USER
    except Exception as e:
        logger.error(f"Unsubscribe request failed for chat_id #{chat_id}: {e}")


def notify(has_electricity: bool):
    if has_electricity is True:
        message = ELECTRICITY_BACK
    else:
        message = ELECTRICITY_GONE

    subscribed_users = get_all_subscribers()

    for user in subscribed_users:
        try:
            bot.send_message(user.chat_id, message)
        except Exception as e:
            logger.error(f"Notification error for chat #{user.chat_id}: {e}")



# Start the bot polling in a separate thread
def start_bot():
    bot.polling(non_stop=True)


if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    pooling_status(config.get("GET_STATUS_ENDPOINT"), notify)
