import telebot
from telebot import types
from dotenv import dotenv_values

config = dotenv_values(".env")
bot = telebot.TeleBot(config.get("BOT_TOKEN"))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Вітаю! Я знаю що у вас з електрикою в домі")

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

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == '__main__':
    # Start the bot
    bot.polling()




