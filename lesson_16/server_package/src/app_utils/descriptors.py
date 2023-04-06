import logging
import sys

logger = logging.getLogger("server")


class Port:
    """
    Класс - дескриптор для номера порта.
    Позволяет использовать только порты с 1023 по 65536.
    При попытке установить неподходящий номер порта останавливает программу
    """

    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            logger.critical(
                "Error starting server."
                " The port must be between 1024 and 65535"
            )
            sys.exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
