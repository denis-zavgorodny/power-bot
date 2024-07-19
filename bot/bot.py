import telebot
from telebot import types
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")
bot = telebot.TeleBot(config.get("BOT_TOKEN"))
bot.delete_my_commands()


GET_STATUS = "Що по світлу?"
SUBSCRIBE = "Отримувати статуси"

greating = """
    Вітаю! 
Я можу дізнаватись для вас чи є світло в домі.

А ще я можу відправляти вам повідомлення коли світло зʼявляється чи зникає.
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row(types.KeyboardButton(GET_STATUS), types.KeyboardButton(SUBSCRIBE))

    bot.reply_to(message, greating, reply_markup=markup)

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

# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

@bot.message_handler(func=lambda message: message.text == GET_STATUS)
def get_status(message):
    response = requests.get(config.get("GET_STATUS_ENDPOINT"))

    if response.status_code == 200:
        bot.reply_to(message, "💡💡💡 Світло є!")
    else:
        bot.reply_to(message, "🔦 Світла немає. Готуйте ліхтарик.")


@bot.message_handler(func=lambda message: message.text == SUBSCRIBE)
def get_status(message):
    bot.reply_to(message, "Ще не працює, але от от вже буде!")

if __name__ == '__main__':
    # Start the bot
    bot.polling()




