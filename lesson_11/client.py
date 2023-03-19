import argparse
import json
import logging
import socket
import sys
import threading
import time
from json import JSONDecodeError

import log.client_log_config  # noqa
import settings
from log.client_log_config import LOGGER_NAME
from metaclasses import ClientVerifier
from utils import FunctionLog

logger = logging.getLogger(LOGGER_NAME)


@FunctionLog(logger)
def send_data(connection, data):
    """
    function for sent data to server
    :param connection: connection to server
    :param data: dict
    :return: None
    """

    js_message = json.dumps(data)
    message = js_message.encode(settings.ENCODING_VAR)
    connection.send(message)


@FunctionLog(logger)
def receive_data(connection):
    """
    receive data from server
    :param
    connection: connection to server
    :return:
    json_data: json
        return json data
    """
    logger.debug("Waiting data from server....")
    data = connection.recv(settings.MAX_DATA_LENGTH)
    if data:
        json_data = json.loads(data.decode(settings.ENCODING_VAR))
        return json_data


@FunctionLog(logger)
def create_presence(account_name):
    """
    create presence message
    :param
    account_name: str
        username for presence message
    :return:
    msg: dict
        return presence message
    """

    msg = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {"account_name": account_name, "status": "Yep, I am here!"},
    }

    return msg


class MessageReceiver(metaclass=ClientVerifier):
    def __init__(self, sock, user_name):
        self.sock = sock
        self.user_name = user_name
        self.thread = None

    def process_message_from_server(self):
        """
        process message from another users
        """
        print("Ждем сообщения от пользователей...")
        error_count = 0
        while True:
            if error_count > settings.MAX_ERROR_COUNT:
                self.sock.close()
                logger.error("To many server errors, clients closed")
                break

            try:
                message = receive_data(self.sock)
                if not message:
                    logger.debug("Received 0 byte, perhaps disconnect from server. Client closed.")
                    time.sleep(0.5)
                    raise ConnectionError
                if (
                    "action" in message
                    and message["action"] == "msg"
                    and "from" in message
                    and "message" in message
                    and "to" in message
                    and message["to"] == self.user_name
                ):
                    print(f"\n Получено сообщение от пользователя: {message['from']} \n {message['message']}")
                    logger.debug("Message: %s from user: %s", message["message"], message["from"])
                else:
                    logger.error("Message from server %s", message)
            except JSONDecodeError as e:
                logger.critical("Json decode error, %s", e)
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError) as e:
                logger.critical("Disconnect from server, %s", e)
                break

    @FunctionLog(logger)
    def run(self):
        self.thread = threading.Thread(target=self.process_message_from_server)
        self.thread.daemon = True
        self.thread.start()


class MessageSender(metaclass=ClientVerifier):
    def __init__(self, sock, user_name):
        self.sock = sock
        self.user_name = user_name
        self.thread = None

    @FunctionLog(logger)
    def create_user_message(self, message, to_user, account_name="Guest"):
        """
        function create message by protocol
        :return
            message_dict = {
                "action": "msg",
                "time": time.time(),
                "from": message from account_name,
                "message": message,
                 "to": sent message to user,
            }
        """

        message_dict = {
            "action": "msg",
            "time": time.time(),
            "from": account_name,
            "message": message,
            "to": to_user,
        }
        logger.debug("Message dict created: %s", message_dict)
        return message_dict

    @FunctionLog(logger)
    def create_quit_message(self):
        """
        function create message by protocol
        :return
            message_dict = {
                "action": "quit",
                "time": time.time(),
            }
        """
        message_dict = {
            "action": "quit",
            "time": time.time(),
        }
        logger.debug("Message dict created: %s", message_dict)
        return message_dict

    def user_interface(self):
        """
        Function for support user interface
        """
        help_text = (
            f"Введите команду {settings.ALLOWED_ACTION_LIST} \n" "msg - для отправки сообщения\n" "quit - для выхода"
        )
        print(help_text)
        while True:
            try:
                time.sleep(0.5)
                action = input(f"Введите команду {settings.ALLOWED_ACTION_LIST}: ")
                if action not in settings.ALLOWED_ACTION_LIST:
                    print("Неправильная команда: \n", help_text)
                    continue
                if action == "msg":
                    msg = input("Ваше сообщение: ")
                    if not msg:
                        continue
                    to_user = input("Кому отправить: ")
                    send_data(self.sock, self.create_user_message(msg, to_user, account_name=self.user_name))
                    print("Сообщение успешно отправлено.")
                    logger.debug("Sent to server: %s", msg)
                if action == "quit":
                    send_data(self.sock, self.create_quit_message())
                    time.sleep(0.5)
                    self.sock.close()
                    print("Подключение закрыто")
                    break

            except JSONDecodeError as e:
                logger.critical("Json decode error, %s", e)
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError) as e:
                logger.critical("Disconnect from server, %s", e)
                break

    @FunctionLog(logger)
    def run(self):
        self.thread = threading.Thread(target=self.user_interface)
        self.thread.daemon = True
        self.thread.start()


@FunctionLog(logger)
def process_response(data):
    """
    process response from server
    :param
    data: json
        answer from server
    :return: str
        decode answer from server
    """

    if "response" in data:
        if data["response"] == 200:
            return "200, OK"
        raise Exception(f"{data['response']}, {data['error']}")
    raise Exception("Can't decode server answer")


@FunctionLog(logger)
def get_params():
    """
    return params from console
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="port", type=int, help="Add port please", default=settings.DEFAULT_SERVER_PORT, nargs="?")
    parser.add_argument(dest="server_ip", type=str, help="Add server ip address please")
    parser.add_argument(dest="user_name", type=str, help="Need user name for chat", default=None, nargs="?")
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error("Error starting client. The port must be between 1024 and 65535")
    if not args.user_name:
        args.user_name = input("Введите имя пользователя: ")
    return args.port, args.server_ip, args.user_name


@FunctionLog(logger)
def main():
    """
    run client with python3 client.py -h
    """
    logger.debug("===== Start working ===== (main)")

    server_port, server_ip, user_name = get_params()
    print("Пытаюсь подключиться к серверу...")
    logger.debug("Trying to connect to the server....")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((server_ip, server_port))
            msg = create_presence(user_name)
            send_data(s, msg)
            data = process_response(receive_data(s))
            print(f"Получено сообщение от сервера: {data}")
            logger.debug("Answer from server: %s", data)
        except JSONDecodeError:
            logger.error("Json decode error")
            sys.exit(1)
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
            logger.critical("Can't connect to server: %s, %s", (server_port, server_ip), e)
            sys.exit(1)
        except Exception as e:
            logger.critical("Something went wrong: %s", e)
            sys.exit(1)
        else:
            # read message thread
            message_receiver = MessageReceiver(s, user_name)
            message_receiver.run()

            # user interface thread
            message_sender = MessageSender(s, user_name)
            message_sender.run()
            logger.debug("Threading is running")

            while True:
                if not (message_receiver.thread.is_alive() and message_sender.thread.is_alive()):
                    break
                time.sleep(1)

    logger.debug("===== End working ===== (main)")


if __name__ == "__main__":
    main()
