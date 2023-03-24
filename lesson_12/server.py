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

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import log.server_log_config  # noqa
import settings
from descriptors import Port
from log.server_log_config import LOGGER_NAME
from metaclasses import ServerVerifier
from server_console_interface import run_server_console_interface
from server_database import ServerStorage
from server_gui import (
    ConfigWindow,
    LoginHistoryWindow,
    MainWindow,
    StatWindow,
    create_active_users_model,
    create_login_history_model,
    create_stat_model,
)
from utils import FunctionLog

logger = logging.getLogger(LOGGER_NAME)

new_connection = False
global_var_lock = threading.Lock()


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, server_port, server_ip, database):
        self.port = server_port
        self.ip = server_ip
        self.server_socket = None
        self.database = database

        # Все клиенты
        self.clients = []

        # имена активных пользователей {"user_name": sock, "another_user_name": sock}
        self.user_names = {}

        # список сообщений вида [{"from": "имя клиента", "message": "сообщение" ,"to": "имя пользователя"}, ]
        self.messages_list = []

        # Поток сервера
        self.thread = None

    def get_client_description(self, sock):
        """
        get client description
        :param sock: socket, client socket
        :return: str
        """
        try:
            # client online, transport parameters included
            return f"Client id: {sock.fileno()}, {sock.getpeername()}"
        except OSError:
            # client offline, no transport parameters
            return f"Client id: {sock.fileno()}"

    @FunctionLog(logger)
    def process_requests(self, r_clients):
        """
        read ready clients
        :param r_clients:list список клиентов готовых к чтению
        """
        global new_connection

        for sock in r_clients:
            try:
                data = self.receive_data(sock)

                if data:
                    self.process_client_message(sock, data)
                    logger.debug("Get request from %s, data: %s", self.get_client_description(sock), data)
            except Exception as e:
                logger.debug(
                    "Function process_requests: client disconnected, %s. System msg: %s. Removed from client list",
                    self.get_client_description(sock),
                    e,
                )
                # remove user from active users
                self.clients.remove(sock)
                for user, conn in self.user_names.items():
                    if conn == sock:
                        self.user_names.pop(user, None)
                        self.database.user_logout(username=user)
                        break
                with global_var_lock:
                    new_connection = True

    @FunctionLog(logger)
    def process_client_message(self, sock, message):
        """
        :param sock: socket connection
        :param message: str message
        """
        global new_connection
        # presence
        if "action" in message and message["action"] == "presence" and "time" in message and "user" in message:
            if message["user"]["account_name"] in self.user_names:
                # user already connected, return answer
                self.send_data(sock, {"response": 402, "time": time.time(), "error": "User already connected."})
                return
            else:
                # if message type presence return answer, add user in user_list
                self.user_names[message["user"]["account_name"]] = sock
                ip, port = sock.getpeername()
                self.database.user_login(username=message["user"]["account_name"], ip_address=ip, port=port)
                self.send_data(sock, {"response": 200, "time": time.time()})
                with global_var_lock:
                    new_connection = True
                return

        # message from user
        if (
            "action" in message
            and message["action"] == "msg"
            and "time" in message
            and "message" in message
            and "from" in message
            and "to" in message
        ):
            if message["to"] in self.user_names:
                # new message add to message list
                self.messages_list.append({"from": message["from"], "message": message["message"], "to": message["to"]})
                return
            else:
                # no user in activ user
                self.send_data(sock, {"response": 400, "time": time.time(), "error": "Wrong user name"})
                return

        # client quit
        if "action" in message and message["action"] == "quit" and "time" in message:
            raise Exception(f"Disconnect user by quit command: {self.get_client_description(sock)}")

        # get list contacts
        if (
            "action" in message
            and message["action"] == "get_contacts"
            and "time" in message
            and "user_login" in message
            and self.user_names[message["user_login"]] == sock
        ):
            contact_list = self.database.get_user_contacts(message["user_login"])
            self.send_data(sock, {"response": 202, "alert": contact_list})
            return

        # add contact
        if (
            "action" in message
            and message["action"] == "add_contact"
            and "time" in message
            and "user_id" in message
            and self.user_names[message["user_id"]] == sock
            and "user_login" in message
        ):
            try:
                self.database.add_contact(message["user_id"], message["user_login"])
            except Exception as e:
                logger.debug(f"Contact not added {e}")
                self.send_data(sock, {"response": 400, "time": time.time(), "error": str(e)})
            else:
                self.send_data(sock, {"response": 200})
            return

        # delete contact
        if (
            "action" in message
            and message["action"] == "del_contact"
            and "time" in message
            and "user_id" in message
            and self.user_names[message["user_id"]] == sock
            and "user_login" in message
        ):
            try:
                self.database.delete_contact(message["user_id"], message["user_login"])
            except Exception as e:
                logger.debug(f"Contact not deleted {e}")
                self.send_data(sock, {"response": 400, "time": time.time(), "error": str(e)})
            else:
                self.send_data(sock, {"response": 200})
            return

        # can't decode message
        self.send_data(sock, {"response": 400, "time": time.time(), "error": "Bad request."})

    @FunctionLog(logger)
    def write_responses(self):
        """
        sent message to waiting clients
        """

        for message in self.messages_list:
            message_dict = {
                "action": "msg",
                "time": time.time(),
                "from": message["from"],
                "message": message["message"],
                "to": message["to"],
            }
            destination_socket = self.user_names[message["to"]]
            try:
                self.send_data(destination_socket, message_dict)
                logger.debug(
                    "Sent response to %s, data: %s", self.get_client_description(destination_socket), message_dict
                )
            except:
                logger.debug(
                    "Client disconnected: %s. Removed from activ client list",
                    self.get_client_description(destination_socket),
                )
                destination_socket.close()
                self.clients.remove(destination_socket)
                for user, conn in self.user_names.items():
                    if conn == destination_socket:
                        self.user_names.pop(user, None)
                        break
            else:
                # Если обмен успешен обновляем статистику
                self.database.update_user_statistic(message["from"], message["to"])

    @FunctionLog(logger)
    def send_data(self, sock, data):
        js_message = json.dumps(data)
        message = js_message.encode(settings.ENCODING_VAR)

        sock.send(message)

    @FunctionLog(logger)
    def receive_data(self, sock):
        try:
            data = sock.recv(settings.MAX_DATA_LENGTH)
            json_data = json.loads(data.decode(settings.ENCODING_VAR))
        except JSONDecodeError:
            return "NonJsonMessage"
        return json_data

    def init_server_socket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self.ip, self.port))
            server_socket.listen(settings.MAX_CONNECTIONS)
            server_socket.settimeout(settings.SERVER_TIMEOUT)
            logger.debug("Server with params %s,  is starting...", server_socket.getsockname())

        except Exception as e:
            logger.critical("Error starting server %s", e)
            raise Exception(f"Error starting server {e}")

        return server_socket

    def main_loop(self):
        self.server_socket = self.init_server_socket()
        while True:
            self.messages_list.clear()
            try:
                # Проверка подключений
                conn, addr = self.server_socket.accept()
            except OSError:
                # Никто не подключился
                pass
            else:
                logger.debug("Connect from client accepted: %s", self.get_client_description(conn))
                self.clients.append(conn)
            finally:
                # Проверить наличие событий ввода вывода
                wait = 1
                ready_to_read_clients = []
                ready_to_write_clients = []
                try:
                    ready_to_read_clients, ready_to_write_clients, clients_with_errors = select.select(
                        self.clients,
                        self.clients,
                        [],
                        wait,
                    )
                except OSError:
                    # Ничего не делать, если какой-то клиент отключился
                    pass

                if ready_to_read_clients:
                    self.process_requests(ready_to_read_clients)
                if self.messages_list and ready_to_write_clients:
                    self.write_responses()

    @FunctionLog(logger)
    def run(self):
        self.thread = threading.Thread(target=self.main_loop)
        self.thread.daemon = True
        self.thread.start()

    def close(self):
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()


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


def main():
    """
    run server with python3 server.py -h

    """
    logger.debug("===== Start working ===== (main)")
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию.
    server_port, server_listen_ip = get_params(config["SETTINGS"]["Default_port"], config["SETTINGS"]["Listen_Address"])
    database = ServerStorage(os.path.join(config["SETTINGS"]["Database_path"], config["SETTINGS"]["Database_file"]))

    server = Server(server_port, server_listen_ip, database)
    server.run()

    # Ждем запуск сервера, если не запустился выходим
    time.sleep(0.5)
    if not server.thread.is_alive():
        exit(1)

    # GUI or console?
    choice = input("Run server GUI? y/n: ")
    if choice.lower().find("y") == -1:
        run_server_console_interface(server=server, database=database)

    # work with GUI start here
    # Создаём графическое окружение для сервера:

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage("Server Working")
    main_window.active_clients_table.setModel(create_active_users_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющая список подключённых, проверяет флаг подключения, и если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(create_active_users_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with global_var_lock:
                new_connection = False

    # Функция создающая окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = StatWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающая окно истории подключений
    def show_login_history():
        global stat_window
        stat_window = LoginHistoryWindow()
        stat_window.history_table.setModel(create_login_history_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающая окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config["SETTINGS"]["Database_path"])
        config_window.db_file.insert(config["SETTINGS"]["Database_file"])
        config_window.port.insert(config["SETTINGS"]["Default_port"])
        config_window.ip.insert(config["SETTINGS"]["Listen_Address"])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config["SETTINGS"]["Database_path"] = config_window.db_path.text()
        config["SETTINGS"]["Database_file"] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, "Ошибка", "Порт должен быть числом")
        else:
            config["SETTINGS"]["Listen_Address"] = config_window.ip.text()
            if 1023 < port < 65536:
                config["SETTINGS"]["Default_port"] = str(port)
                print(port)
                with open("server.ini", "w") as conf:
                    config.write(conf)
                    message.information(config_window, "OK", "Настройки успешно сохранены!")
            else:
                message.warning(config_window, "Ошибка", "Порт должен быть от 1024 до 65536")

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с функциями
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_stat_button.triggered.connect(show_statistics)
    main_window.show_login_history_button.triggered.connect(show_login_history)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == "__main__":
    main()
