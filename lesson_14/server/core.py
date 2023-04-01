import binascii
import hashlib
import hmac
import json
import logging
import select
import socket
import threading
import time


import log.server_log_config  # noqa
import settings
from descriptors import Port
from log.server_log_config import LOGGER_NAME
from utils import FunctionLog, login_required

logger = logging.getLogger(LOGGER_NAME)


class ServerCore:
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
        # Флаг продолжения работы
        self.running = True

    def main_loop(self):
        self.server_socket = self.init_server_socket()
        while self.running:
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
        logger.debug("====== Start Server shutdown =======")
        self.running = False
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()

    def client_close(self, sock):
        # remove user from active users, logout, close socket
        self.clients.remove(sock)
        for user, conn in self.user_names.items():
            if conn == sock:
                self.user_names.pop(user, None)
                self.database.user_logout(username=user)
                break
        sock.close()

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
        # global new_connection

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
                # Remove user from active users
                self.client_close(sock)

    @FunctionLog(logger)
    @login_required
    def process_client_message(self, sock, message):
        """
        :param sock: socket connection
        :param message: str message
        """

        # presence
        if "action" in message and message["action"] == "presence" and "time" in message and "user" in message:
            try:
                self.authorise_user(sock, message)
            except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
                logger.debug(
                    "Function authorise_user: client disconnected, %s. System msg: %s. Removed from client list",
                    self.get_client_description(sock),
                    e,
                )
                self.clients.remove(sock)
                sock.close()
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

    # Авторизация пользователя
    def authorise_user(self, sock, message):
        # presence message
        if message["user"]["account_name"] in self.user_names:
            # user already connected, return answer
            self.send_data(sock, {"response": 402, "time": time.time(), "error": "User already connected."})

        elif not self.database.user_exists(message["user"]["account_name"]):
            response = {"response": 404, "time": time.time(), "error": "User not registered"}
            logger.debug(f"Unknown username, sending {response}")
            self.send_data(sock, response)
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug("Correct username: %s, starting passwd check.", message["user"]["account_name"])
            logger.debug("Sent 401 response")
            # Иначе отвечаем 401 need authenticate
            self.send_data(sock, {"response": 401, "time": time.time(), "error": "Need authenticate"})
            answer = self.receive_data(sock)
            if (
                "action" in answer
                and answer["action"] == "authenticate"
                and "time" in message
                and "user" in message
                and "account_name" in answer["user"]
                and "password" in answer["user"]
                and "account_name"
                and "password"
                and message["user"]["account_name"] == answer["user"]["account_name"]
            ):
                user_passwd_hash = self.database.get_hash(name=message["user"]["account_name"])
                new_user_passwd_hash = self.get_hash(
                    username=message["user"]["account_name"], password=answer["user"]["password"]
                )
                if hmac.compare_digest(user_passwd_hash, new_user_passwd_hash):
                    self.user_names[message["user"]["account_name"]] = sock
                    ip, port = sock.getpeername()
                    self.database.user_login(username=message["user"]["account_name"], ip_address=ip, port=port)
                    self.send_data(sock, {"response": 200, "time": time.time()})
                else:
                    self.send_data(
                        sock,
                        {"response": 402, "time": time.time(), "error": "wrong password or no account with that name"},
                    )
                    self.clients.remove(sock)
                    sock.close()
            else:
                self.send_data(sock, {"response": 400, "time": time.time(), "error": "Bad request."})
                self.clients.remove(sock)
                sock.close()

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
                # Remove client from connected users
                self.client_close(destination_socket)

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
        data = None
        try:
            data = sock.recv(settings.MAX_DATA_LENGTH)
            json_data = json.loads(data.decode(settings.ENCODING_VAR))
        except json.JSONDecodeError:
            logger.critical("NonJsonMessage: %str", data)
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

    def get_hash(self, username, password):
        # Генерируем хэш пароля, в качестве соли будем использовать логин в нижнем регистре.
        passwd_bytes = password.encode("utf-8")
        salt = username.lower().encode("utf-8")
        passwd_hash = hashlib.pbkdf2_hmac("sha512", passwd_bytes, salt, 10000)
        return binascii.hexlify(passwd_hash)


if __name__ == "__main__":
    pass
