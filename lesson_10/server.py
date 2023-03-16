import argparse
import json
import logging
import select
import socket
import time
from json import JSONDecodeError

import log.server_log_config  # noqa
import settings
from descriptors import Port
from log.server_log_config import LOGGER_NAME
from metaclasses import ServerVerifier
from utils import FunctionLog

logger = logging.getLogger(LOGGER_NAME)


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, server_port, server_ip):
        self.port = server_port
        self.ip = server_ip

        # Все клиенты
        self.clients = []

        # имена активных пользователей {"user_name": sock, "another_user_name": sock}
        self.user_names = {}

        # список сообщений вида [{"from": "имя клиента", "message": "сообщение" ,"to": "имя пользователя"}, ]
        self.messages_list = []

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

        for sock in r_clients:
            try:
                data = self.receive_data(sock)

                if data:
                    self.process_client_message(sock, data)
                    logger.debug("Get request from %s, data: %s", self.get_client_description(sock), data)
            except Exception:
                logger.debug(
                    "Function process_requests: client disconnected, %s. Removed from client list",
                    self.get_client_description(sock),
                )
                self.clients.remove(sock)
                # remove user from active users
                for user, conn in self.user_names.items():
                    if conn == sock:
                        self.user_names.pop(user, None)
                        break

    @FunctionLog(logger)
    def process_client_message(self, sock, message):
        """
        :param sock: socket connection
        :param message: str message
        """
        if "action" in message and message["action"] == "presence" and "time" in message and "user" in message:
            if message["user"]["account_name"] in self.user_names:
                # user already connected, return answer
                self.send_data(sock, {"response": 402, "time": time.time(), "error": "User already connected."})
                return
            else:
                # if message type presence return answer, add user in user_list
                self.user_names[message["user"]["account_name"]] = sock
                self.send_data(sock, {"response": 200, "time": time.time()})
                return

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
                self.send_data(
                    sock,
                    {"response": 400, "time": time.time(), "error": "Wrong user name"},
                )
                return

        if "action" in message and message["action"] == "quit" and "time" in message:
            raise Exception(f"Disconnect user by quit command: {self.get_client_description(sock)}")

        # can't decode message
        self.send_data(
            sock,
            {"response": 400, "time": time.time(), "error": "Bad request."},
        )

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
        server_socket = self.init_server_socket()
        while True:
            self.messages_list.clear()
            try:
                # Проверка подключений
                conn, addr = server_socket.accept()
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
def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        dest="port",
        type=int,
        help="Add port please '-p'",
        default=settings.DEFAULT_SERVER_PORT,
    )
    parser.add_argument(
        "-a",
        dest="server_listen_ip",
        type=str,
        help="Add listen ip address please '-a'",
        default=settings.DEFAULT_SERVER_LISTEN_ADDRESS,
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
    server_port, server_listen_ip = get_params()
    server = Server(server_port, server_listen_ip)
    server.main_loop()


if __name__ == "__main__":
    main()
