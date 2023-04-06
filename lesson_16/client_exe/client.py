import argparse
import logging
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

import log.client_log_config
from app_utils.settings import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT
from app_utils.utils import log
from client.client_database import ClientDatabase
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport

logger = logging.getLogger("client")


@log(logger)
def arg_parser():
    """
    Парсер аргументов командной строки,
    возвращает кортеж из 2 элементов адрес сервера, порт.
    Выполняет проверку на корректность номера порта.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", dest="port", default=DEFAULT_SERVER_PORT, type=int, nargs="?"
    )
    parser.add_argument(
        "-a", dest="addr", default=DEFAULT_SERVER_ADDRESS, nargs="?"
    )
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f"Попытка запуска клиента с неподходящим номером порта:"
            f" {server_port}."
            f" Допустимы адреса с 1024 до 65535. Клиент завершается."
        )
        sys.exit(1)

    return server_address, server_port


# Основная функция клиента
if __name__ == "__main__":
    # Загружаем параметры командной строки
    server_address, server_port = arg_parser()

    # Создаём клиентское приложение
    client_app = QApplication(sys.argv)
    # Запросим имя пользователя и пароль
    start_dialog = UserNameDialog()
    client_app.exec_()
    # Если пользователь ввёл имя и нажал ОК,
    # то сохраняем ведённое и удаляем объект, иначе выходим
    if start_dialog.ok_pressed:
        client_name = start_dialog.client_name.text()
        client_password = start_dialog.client_passwd.text()
        del start_dialog
    else:
        sys.exit(0)

    # Записываем логи
    logger.info(
        f"Запущен клиент с парамерами: адрес сервера:"
        f" {server_address} , порт: {server_port},"
        f" имя пользователя: {client_name}"
    )

    # Создаём объект базы данных
    database = ClientDatabase(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(
            port=server_port,
            ip_address=server_address,
            database=database,
            username=client_name,
            password=client_password,
        )
    except Exception as error:
        print(error)
        sys.exit(1)
    else:
        transport.daemon = True
        transport.start()

        # Создаём GUI
        main_window = ClientMainWindow(database=database, transport=transport)
        main_window.make_connection(transport)
        main_window.setWindowTitle(
            f"Чат Программа alpha release - {client_name}"
        )
        client_app.exec_()

        # Раз графическая оболочка закрылась, закрываем транспорт
        transport.transport_shutdown()
        transport.join()
