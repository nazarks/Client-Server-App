class ServerError(Exception):
    """
    Класс - исключение, для обработки ошибок сервера.
    При генерации требует строку с описанием ошибки.
    """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class InternalException(Exception):
    """
    Класс - исключение, для обработки внутреннего исключения
    При генерации требует строку с описанием ошибки.
    """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
