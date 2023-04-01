import logging

logger = logging.getLogger("server")


class Port:
    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            logger.critical("Error starting server. The port must be between 1024 and 65535")
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
