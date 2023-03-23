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
from client_database import ClientDatabase
from log.client_log_config import LOGGER_NAME
from metaclasses import ClientVerifier
from utils import FunctionLog, datetime_from_utc_to_local

logger = logging.getLogger(LOGGER_NAME)

sock_lock = threading.Lock()
database_lock = threading.Lock()


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
    def __init__(self, sock, user_name, database):
        self.sock = sock
        self.user_name = user_name
        self.database = database
        self.thread = None

    def process_message_from_server(self):
        """
        process message from another users
        """
        print("Ждем сообщения от пользователей...")
        error_count = 0
        while True:
            # Освобождаем сокет
            time.sleep(1)
            if error_count > settings.MAX_ERROR_COUNT:
                self.sock.close()
                logger.error("To many server errors, clients closed")
                break

            with sock_lock:
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
                except OSError as err:
                    if err.errno:
                        logger.critical("Disconnect from server, %s", err)
                        break
                    # Timeout освобождаем сокет
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError) as e:
                    logger.critical("Disconnect from server, %s", e)
                    break

    @FunctionLog(logger)
    def run(self):
        self.thread = threading.Thread(target=self.process_message_from_server)
        self.thread.daemon = True
        self.thread.start()


class MessageSender(metaclass=ClientVerifier):
    def __init__(self, sock, user_name, database):
        self.sock = sock
        self.user_name = user_name
        self.database = database
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

    def sent_message_to_user(self, msg, to_user, account_name="Guest"):
        message = self.create_user_message(msg, to_user, account_name=account_name)
        with sock_lock:
            try:
                send_data(self.sock, message)
            except OSError as err:
                if err.errno:
                    logger.critical("Disconnect from server %s", str(err))
                    exit(1)
                else:
                    logger.error("Message not sent, by timeout %s", str(message))
            else:
                print("Сообщение успешно отправлено.")
                logger.debug("Message sent %s", message)
                with database_lock:
                    self.database.save_message(from_user=account_name, to_user=to_user, message=msg.strip())

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

    def edit_contacts(self):
        ans = input("Для удаления введите del, для добавления add: ")
        if ans == "del":
            contact = input("Введите имя удаляемого контакта: ")
            contact_deleted = False
            with sock_lock:
                try:
                    delete_contact(self.sock, self.user_name, contact)
                    contact_deleted = True
                except Exception as e:
                    print(f"Контакт не удален: {contact}, ошибка {e}")
                    logger.error(f"Contact not deleted: {e}")
            # Если на сервер удалили, удаляем локально
            if contact_deleted:
                with database_lock:
                    self.database.delete_contact(contact)
                print(f"Контакт успешно удален: {contact}")

        elif ans == "add":
            contact = input("Введите имя создаваемого контакта: ")
            # Добавляем контакт на сервер
            contact_added = False
            with sock_lock:
                try:
                    add_contact(self.sock, self.user_name, contact)
                    contact_added = True
                except Exception as e:
                    print(f"Контакт не добавлен: {contact}, ошибка {e}")
                    logger.error(f"Contact not added: {e}")
            # Если на сервер добавили добавляем локально
            if contact_added:
                with database_lock:
                    self.database.add_contact(contact)
                print(f"Контакт успешно добавлен: {contact}")

    def get_history(self):
        # ask = input("Показать входящие сообщения - in, исходящие - out, все - просто Enter: ")
        with database_lock:
            history_list = self.database.get_messages()
        return history_list

    def user_interface(self):
        """
        Function for support user interface
        """
        help_text = f"Введите команду: {settings.CLIENT_ALLOWED_COMMAND_LIST} \n"
        time.sleep(0.5)
        while True:
            try:
                action = input(f"Введите команду {settings.CLIENT_ALLOWED_COMMAND_LIST}: \n")
                if action not in settings.CLIENT_ALLOWED_COMMAND_LIST:
                    print("Неправильная команда: \n", help_text)
                    continue
                # Отправить сообщение
                if action == "msg":
                    msg = input("Ваше сообщение: ")
                    if not msg:
                        continue
                    to_user = input("Кому отправить: ")
                    self.sent_message_to_user(msg, to_user, account_name=self.user_name)

                # Закрыть приложение
                elif action == "quit":
                    send_data(self.sock, self.create_quit_message())
                    time.sleep(0.5)
                    self.sock.close()
                    print("Подключение закрыто")
                    break
                # Вывести список контактов
                elif action == "contacts":
                    with database_lock:
                        contacts_list = self.database.get_contacts()
                    for contact in contacts_list:
                        print(contact)
                # Добавить удалить контакт
                elif action == "edit":
                    self.edit_contacts()
                elif action == "history":
                    message_list = self.get_history()
                    print("Сообщения найдены: \n")
                    for message in message_list:
                        print(
                            f"От: {message[0]} к: {message[1]} дата и время: {datetime_from_utc_to_local(message[3])}\n"
                            f"сообщение: {message[2]}"
                        )

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


# Функция запрос контакт листа
def contacts_list_request(sock, name):
    logger.debug(f"User contact list for: {name}")
    request = {"action": "get_contacts", "time": time.time(), "user_login": name}
    logger.debug(f"Request to server {request}")
    send_data(sock, request)
    answer = receive_data(sock)
    logger.debug(f"Получен ответ {answer}")
    if "response" in answer and answer["response"] == 202:
        return answer["alert"]
    else:
        raise Exception("Server error")


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    logger.debug(f"Contact for create {contact}")
    request = {"action": "add_contact", "time": time.time(), "user_id": username, "user_login": contact}
    logger.debug(f"Request to server {request}")
    send_data(sock, request)
    answer = receive_data(sock)
    logger.debug(f"Ответ {request}")
    if "response" in answer and answer["response"] == 200:
        print("Удачное создание контакта.")
    else:
        raise Exception(f"Error add contact: {answer}")


# Функция удаления пользователя из списка контактов
def delete_contact(sock, username, contact):
    logger.debug(f"Contact to delete {contact}")
    request = {"action": "del_contact", "time": time.time(), "user_id": username, "user_login": contact}
    send_data(sock, request)
    answer = receive_data(sock)
    if "response" in answer and answer["response"] == 200:
        print(f"Контакт удален {contact}")
    else:
        raise Exception(f"Error delete contact {answer}")


# Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    try:
        contacts_list = contacts_list_request(sock, username)
    except Exception as e:
        logger.error(f"Error request user contact list. {e}")
    else:
        for contact in contacts_list:
            database.add_contact(contact=contact)


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
            s.settimeout(1)
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
            database = ClientDatabase(owner=user_name)
            database_load(s, database, user_name)

            # read message thread
            message_receiver = MessageReceiver(s, user_name, database)
            message_receiver.run()

            # user interface thread
            message_sender = MessageSender(s, user_name, database)
            message_sender.run()
            logger.debug("Threading is running")

            while True:
                if not (message_receiver.thread.is_alive() and message_sender.thread.is_alive()):
                    break
                time.sleep(1)

    logger.debug("===== End working ===== (main)")


if __name__ == "__main__":
    main()
