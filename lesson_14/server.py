import argparse
import configparser
import json
import logging
import os
import select
import socket
import sys
import threading
import time
from json import JSONDecodeError

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import log.server_log_config  # noqa
import settings
from log.server_log_config import LOGGER_NAME
from server.core import ServerCore
from server.main_window import MainWindow
from server.server_console_interface import run_server_console_interface
from server.server_database import ServerStorage

# from server_gui import (
#     ConfigWindow,
#     LoginHistoryWindow,
#     MainWindow,
#     StatWindow,
#     create_active_users_model,
#     create_login_history_model,
#     create_stat_model,
# )
from utils import FunctionLog

logger = logging.getLogger(LOGGER_NAME)


@FunctionLog(logger)
def get_params(default_port, default_address):
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
        parser.error("Error starting server. The port must be between 1024 and 65535")

    return args.port, args.server_listen_ip


@FunctionLog(logger)
def config_load():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
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

    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию.
    database = ServerStorage(os.path.join(config["SETTINGS"]["Database_path"], config["SETTINGS"]["Database_file"]))

    server_port, server_ip = get_params(config["SETTINGS"]["Default_port"], config["SETTINGS"]["Listen_Address"])
    server = ServerCore(server_port=server_port, server_ip=server_ip, database=database)
    server.run()

    # Ждем запуск сервера, если не запустился выходим
    time.sleep(0.5)
    if not server.thread.is_alive():
        exit(1)

    # GUI or console?
    choice = input("Run server GUI? y/n: ")
    if choice.lower().find("y") == -1:
        run_server_console_interface(server=server, database=database)

    server_app = QApplication(sys.argv)
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(database=database, server=server, config=config)

    # Запускаем GUI
    server_app.exec_()

    # По закрытию окон останавливаем обработчик сообщений
    server.running = False


if __name__ == "__main__":
    main()
