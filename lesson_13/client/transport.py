import json
import logging
import socket
import sys
import threading
import time
from json import JSONDecodeError

from PyQt5.QtCore import QObject, pyqtSignal

sys.path.append("../")  # noqa
import log.client_log_config  # noqa
import settings
from log.client_log_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

sock_lock = threading.Lock()
database_lock = threading.Lock()


# Класс - Транспорт, отвечает за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # Имя пользователя который подключается к серверу (owner)
        self.username = username
        # Сокет для работы с сервером
        self.transport = None
        self.server_port = port
        self.server_ip = ip_address
        # Устанавливаем соединение:
        self.connection_init(ip_address, port)
        # Обновляем таблицу контактов
        try:
            self.contact_list_update(self.username)
        except OSError as err:
            if err.errno:
                logger.critical(f"Потеряно соединение с сервером.")
                raise Exception("Потеряно соединение с сервером!")
            logger.error("Timeout соединения при обновлении списков пользователей.")
        except json.JSONDecodeError:
            logger.critical(f"Потеряно соединение с сервером.")
            raise Exception("Потеряно соединение с сервером!")
            # Флаг продолжения работы транспорта.
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, ip, port):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.transport.settimeout(3)

        try:
            self.transport.connect((ip, port))
        except (OSError, ConnectionRefusedError):
            logger.critical("Не удалось установить соединение с сервером")
            raise Exception("Не удалось установить соединение с сервером")

        logger.debug("Установлено соединение с сервером")

        try:
            msg = self.create_presence(self.username)
            with sock_lock:
                logger.debug("Sent data to server: %s", msg)
                self.send_data(msg)
                data = self.process_presence_response(self.receive_data())
                logger.debug("Answer from server: %s", data)
        except JSONDecodeError:
            logger.error("Json decode error")
            sys.exit(1)
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
            logger.critical("Can't connect to server: %s, %s", (ip, port), e)
            sys.exit(1)
        except Exception as e:
            logger.critical("Something went wrong: %s", e)
            sys.exit(1)

    def send_data(self, data):  # noqa
        """
        function for sent data to server
        :param data: dict
        :return: None
        """

        js_message = json.dumps(data)
        message = js_message.encode(settings.ENCODING_VAR)
        self.transport.send(message)

    def receive_data(self):  # noqa
        """
        receive data from server
        :param
        connection: connection to server
        :return:
        json_data: json
            return json data
        """

        data = self.transport.recv(settings.MAX_DATA_LENGTH)
        if data:
            json_data = json.loads(data.decode(settings.ENCODING_VAR))
            return json_data

    def create_presence(self, account_name):  # noqa
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
        logger.debug("Presence created: %s", msg)
        return msg

    def process_presence_response(self, data):  # noqa
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

        raise Exception(f"Can't decode server answer {data}")

    def contact_list_update(self, name):
        contacts = self.contact_list_request(name)
        for contact in contacts:
            self.database.add_contact(contact)
            logger.debug(f"Contact added to database: {contact}")

    # Функция запрос контакт листа
    def contact_list_request(self, name):
        logger.debug(f"User contact list for: {name}")
        request = {"action": "get_contacts", "time": time.time(), "user_login": name}
        logger.debug(f"Request to server {request}")
        self.send_data(request)
        answer = self.receive_data()
        logger.debug(f"Получен ответ {answer}")
        if "response" in answer and answer["response"] == 202:
            return answer["alert"]
        else:
            raise Exception("Server error")

    def process_message_from_server(self, message):
        logger.debug(f"Разбор сообщения от сервера: {message}")

        if (
            "action" in message
            and message["action"] == "msg"
            and "from" in message
            and "message" in message
            and "to" in message
            and message["to"] == self.username
        ):
            print(f"\n Получено сообщение от пользователя: {message['from']} \n {message['message']}")
            logger.debug("Message: %s from user: %s", message["message"], message["from"])
            # В историю сообщений
            self.database.save_message(from_user=message["from"], to_user=self.username, message=message["message"])
            self.new_message.emit(message["from"])
            # save_message(self, from_user, to_user, message):
        elif "response" in message and message["response"] == 200:
            return
        elif "response" in message and message["response"] == 400:
            logger.error("Response from server: %s", message)
            raise Exception(f"Response from server: {message}")
        else:
            logger.error("Can't decode message from server %s", message)

    # Функция добавления пользователя в контакт лист
    def add_contact(self, contact):
        logger.debug(f"Contact for create {contact}")
        request = {"action": "add_contact", "time": time.time(), "user_id": self.username, "user_login": contact}
        logger.debug(f"Request to server {request}")
        with sock_lock:
            self.send_data(request)
            answer = self.receive_data()
        logger.debug(f"Ответ {answer}")
        if "response" in answer and answer["response"] == 200:
            print("Удачное создание контакта.")
        else:
            logger.error("Error add contact %s: ", str(answer))
            raise Exception(f"Error add contact: {answer}")

    # Функция удаления пользователя из списка контактов
    def delete_contact(self, contact):
        logger.debug(f"Contact to delete {contact}")
        request = {"action": "del_contact", "time": time.time(), "user_id": self.username, "user_login": contact}
        with sock_lock:
            self.send_data(request)
            answer = self.receive_data()
        if "response" in answer and answer["response"] == 200:
            print(f"Контакт удален {contact}")
        else:
            logger.error("Error add contact %s: ", str(answer))
            raise Exception(f"Error delete contact {answer}")

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

    def transport_shutdown(self):
        self.running = False
        message = self.create_quit_message()
        with sock_lock:
            try:
                self.send_data(message)
            except OSError:
                pass
        logger.debug("Транспорт завершает работу.")
        time.sleep(0.5)

    def create_user_message(self, message, to_user):
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

        message_dict = {"action": "msg", "time": time.time(), "from": self.username, "message": message, "to": to_user}
        logger.debug("Message dict created: %s", message_dict)
        return message_dict

    def sent_message_to_user(self, msg, to_user):
        message = self.create_user_message(msg, to_user)
        with sock_lock:
            logger.debug("Try ro sent: Message %s to_user %s", message, to_user)
            self.send_data(message)
            self.process_message_from_server(self.receive_data())
            logger.debug("Message sent %s", message)

    def run(self):
        logger.debug("Запущен процесс - приёмник сообщений с сервера.")
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            time.sleep(1)
            with sock_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = self.receive_data()
                except OSError as err:
                    if err.errno:
                        logger.critical(f"Потеряно соединение с сервером.")
                        self.running = False
                        self.connection_lost.emit()
                    else:
                        # Timeout освобождаем  сокет
                        pass
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, JSONDecodeError):
                    logger.debug(f"Потеряно соединение с сервером.")
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    logger.debug(f"Принято сообщение с сервера: {message}")
                    if not message:
                        logger.debug("Received 0 byte, perhaps disconnect from server. Client closed.")
                        time.sleep(0.5)
                        raise ConnectionError
                    try:
                        self.process_message_from_server(message)
                    except:
                        pass
                finally:
                    self.transport.settimeout(5)


if __name__ == "__main__":
    from client_database import ClientDatabase

    user = "User1"
    database = ClientDatabase("User1")
    client = ClientTransport(port="7777", ip_address="127.0.0.1", database=database, username=user)
