import logging

logger = logging.getLogger("power-telegram-bot")

logging.basicConfig(
    filename="power-telegram-bot.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_logger():
    return logger
