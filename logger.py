import logging

logger = logging.getLogger("power-telegram-bot")

logging.basicConfig(
    level=logging.INFO,
    filename="power-bot.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_logger():
    return logger
