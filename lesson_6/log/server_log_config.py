import logging
from logging.handlers import TimedRotatingFileHandler
from os import path

LOGGER_NAME = "server"
PATH_TO_LOG = path.join("log", path.join("logs", "server.log"))

# Создаем объект-логгер:
logger = logging.getLogger(LOGGER_NAME)

# Создаем объект форматирования:
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

# Создать файловый обработчик логгирования TimedRotatingFileHandler (можно задать кодировку):
frh = TimedRotatingFileHandler(PATH_TO_LOG, when="D", interval=1, backupCount=7, encoding="utf-8")
frh.setLevel(logging.DEBUG)
frh.setFormatter(formatter)

# Добавить в логгер новый обработчик и установить уровень логгирования
logger.addHandler(frh)
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    logger.info("Тестовый запуск логирования")
