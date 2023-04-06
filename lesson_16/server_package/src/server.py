import argparse
import configparser
import logging
import os
import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import log.server_log_config  # noqa
from app_utils.utils import FunctionLog
from log.server_log_config import LOGGER_NAME
from server.core import ServerCore
from server.main_window import MainWindow
from server.server_console_interface import run_server_console_interface
from server.server_database import ServerStorage

logger = logging.getLogger(LOGGER_NAME)


@FunctionLog(logger)
def get_params(default_port, default_address):
    """
    Парсер аргументов командной строки,
    возвращает кортеж из 2 элементов порт и адрес.
    Выполняет проверку на корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        dest="port",
        type=int,
        help="Add port please '-p'",
        default=default_port,
    )
    parser.add_argument(
        "-a",
        dest="server_listen_ip",
        type=str,
        help="Add listen ip address please '-a'",
        default=default_address,
    )
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error(
            "Error starting server. The port must be between 1024 and 65535"
        )

    return args.port, args.server_listen_ip


@FunctionLog(logger)
def config_load():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    # dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")
    if "SETTINGS" in config:
        return config
    else:
        raise Exception("Can't read config file server.ini")


@FunctionLog(logger)
def main():
    """
    run server with python3 server.py -h

    """
    logger.debug("===== Start working ===== (main)")
    # Загрузка файла конфигурации сервера
    config = config_load()

    # Загрузка параметров командной строки,
    # если нет параметров, то задаём значения по умолчанию.
    database = ServerStorage(
        os.path.join(
            config["SETTINGS"]["Database_path"],
            config["SETTINGS"]["Database_file"],
        )
    )

    server_port, server_ip = get_params(
        config["SETTINGS"]["Default_port"],
        config["SETTINGS"]["Listen_Address"],
    )
    server = ServerCore(
        server_port=server_port, server_ip=server_ip, database=database
    )
    server.run()

    # Ждем запуск сервера, если не запустился выходим
    time.sleep(0.5)
    if not server.thread.is_alive():
        sys.exit(1)

    # GUI or console?
    choice = input("Run server GUI? y/n: ")
    if choice.lower().find("y") == -1:
        run_server_console_interface(server=server, database=database)
        sys.exit(0)

    server_app = QApplication(sys.argv)
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(
        database=database, server=server, config=config
    )  # noqa

    # Запускаем GUI
    server_app.exec_()

    # По закрытию окон останавливаем обработчик сообщений
    server.running = False


if __name__ == "__main__":
    main()
