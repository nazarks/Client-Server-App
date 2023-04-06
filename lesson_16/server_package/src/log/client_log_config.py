import logging
import sys
from os import path

LOGGER_NAME = "client"
PATH_TO_LOG = path.join("log", path.join("logs", "client.log"))

# Создаем объект-логер:
logger = logging.getLogger(LOGGER_NAME)

# Создаем объект форматирования:
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)

# Создать файловый обработчик логирования (можно задать кодировку):
fh = logging.FileHandler(PATH_TO_LOG, encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

# Создать обработчик вывода в консоль:
console = logging.StreamHandler(sys.stderr)
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)

# Добавить в логгер новый обработчик и установить уровень логирования
logger.addHandler(fh)
logger.addHandler(console)
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    pass
