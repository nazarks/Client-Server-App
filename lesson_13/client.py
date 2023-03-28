import argparse
import logging
import sys

from PyQt5.QtWidgets import QApplication

import log.client_log_config
from client.client_database import ClientDatabase
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from settings import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT
from utils import log

logger = logging.getLogger("client")


# Парсер аргументов командной строки
@log(logger)
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("addr", default=DEFAULT_SERVER_ADDRESS, nargs="?")
    parser.add_argument("port", default=DEFAULT_SERVER_PORT, type=int, nargs="?")
    parser.add_argument("-n", "--name", default=None, nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта: {server_port}."
            f" Допустимы адреса с 1024 до 65535. Клиент завершается."
        )
        exit(1)

    return server_address, server_port, client_name


# Основная функция клиента
if __name__ == "__main__":
    # Загружаем параметры командной строки
    server_address, server_port, client_name = arg_parser()

    # Создаём клиентское приложение
    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке, то запросим его
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, иначе выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    # Записываем логи
    logger.info(
        f"Запущен клиент с парамерами: адрес сервера: {server_address} , порт: {server_port},"
        f" имя пользователя: {client_name}"
    )

    # Создаём объект базы данных
    database = ClientDatabase(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(
            port=server_port, ip_address=server_address, database=database, username=client_name
        )
    except Exception as error:
        print(error)
        exit(1)
    else:
        transport.daemon = True
        transport.start()

        # Создаём GUI
        main_window = ClientMainWindow(database=database, transport=transport)
        main_window.make_connection(transport)
        main_window.setWindowTitle(f"Чат Программа alpha release - {client_name}")
        client_app.exec_()

        # Раз графическая оболочка закрылась, закрываем транспорт
        transport.transport_shutdown()
        transport.join()
