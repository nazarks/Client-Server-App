import dis


class ServerVerifier(type):
    """
    Метакласс, проверяющий, что в результирующем классе
    нет клиентских вызовов таких как: connect.
    Также проверяется, что серверный сокет является TCP
    и работает по IPv4 протоколу.
    """

    def __init__(self, clsname, bases, clsdict):
        """
        clsname - экземпляр метакласса - Server
        bases - кортеж базовых классов - ()
        clsdict - словарь атрибутов и методов экземпляра метакласса
        """

        # Список методов, которые используются в функциях класса:
        methods = []
        # Атрибуты, используемые в функциях классов
        attrs = []
        # перебираем ключи
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                # Раз функция разбираем код,
                # получая используемые методы и атрибуты.
                for i in ret:
                    # opname - имя для операции
                    if i.opname in ("LOAD_GLOBAL", "LOAD_METHOD"):
                        if i.argval not in methods:
                            # заполняем список методами,
                            # использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == "LOAD_ATTR":
                        if i.argval not in attrs:
                            # заполняем список атрибутами,
                            # использующимися в функциях класса
                            attrs.append(i.argval)
        # Если обнаружено использование недопустимого метода connect,
        # бросаем исключение:
        if "connect" in methods:
            raise TypeError(
                "Использование метода connect недопустимо в серверном классе"
            )
        # Если сокет не инициализировался константами SOCK_STREAM(TCP)
        # AF_INET(IPv4), тоже исключение.
        if not ("SOCK_STREAM" in attrs and "AF_INET" in attrs):
            raise TypeError("Некорректная инициализация сокета.")
        # Обязательно вызываем конструктор предка:
        super().__init__(clsname, bases, clsdict)


# Метакласс для проверки корректности клиентов:
class ClientVerifier(type):
    """
    Метакласс, проверяющий, что в результирующем классе
    нет серверных вызовов таких как: accept, listen.
    Также проверяется, что сокет не создаётся внутри конструктора класса.
    """

    def __init__(self, clsname, bases, clsdict):
        # Список методов, которые используются в функциях класса:
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция, то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы.
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)

        # Если обнаружено использование недопустимого метода accept,
        # listen, socket бросаем исключение:
        for command in ("accept", "listen", "socket"):
            if command in methods:
                raise TypeError(
                    "В классе обнаружено использование запрещённого метода"
                )
        # Вызов "receive_data" или "send_data"
        # считаем корректным использованием сокетов
        if "receive_data" in methods or "send_data" in methods:
            pass
        else:
            raise TypeError(
                "Отсутствуют вызовы функций, работающих с сокетами."
            )
        super().__init__(clsname, bases, clsdict)
