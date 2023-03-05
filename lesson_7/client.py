import argparse
import json
import logging
import socket
import time
from json import JSONDecodeError
import sys

import log.client_log_config
import settings
from log.client_log_config import LOGGER_NAME
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


@FunctionLog(logger)
def create_message(message, account_name="Guest"):
    """
    function create message by protocol
    :return
        message_dict = {
            "action": "msg",
            "time": time.time(),
            "from": account_name,
            "message": message,
        }
    """

    message_dict = {
        "action": "msg",
        "time": time.time(),
        "from": account_name,
        "message": message,
    }
    logger.debug("Message dict created: %s", message_dict)
    return message_dict


@FunctionLog(logger)
def process_message(message):
    """
    process message from another users
    :param message:
    :return:
    """
    if "action" in message and message["action"] == "msg" and "from" in message and "message" in message:
        logger.debug("Message: %s from user: %s", message["message"], message["from"])
    else:
        logger.error("Wrong message from server %s", message)


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
    parser.add_argument(
        dest="port",
        type=int,
        help="Add port please",
        default=settings.DEFAULT_SERVER_PORT,
        nargs="?",
    )
    parser.add_argument(dest="server_ip", type=str, help="Add server ip address please")
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error("Error starting client. The port must be between 1024 and 65535")

    return args.port, args.server_ip


def main():
    """
    run client with python3 client.py -h
    """
    logger.debug("===== Start working ===== (main)")

    server_port, server_ip = get_params()
    mode = input("Выберете режим работы: 'w' - отправлять сообщения на сервер, 'r' - читать сообщения от сервера: ")
    if mode == "w":
        print("Выбран режим работы - отправка сообщений")
    else:
        print("Выбран режим работы - прием сообщений")
    logger.debug("Trying to connect to the server....")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            try:
                msg = create_presence("Nik")
                send_data(s, msg)
                data = process_response(receive_data(s))
                logger.debug("Answer from server: %s", data)
            except JSONDecodeError:
                logger.error("Json decode error")
                sys.exit(1)
            except Exception as e:
                logger.error(e)
                sys.exit(1)

            while True:
                if mode == "w":
                    msg = input("Ваше сообщение: ")
                    if msg == "e":
                        break
                    send_data(s, create_message(msg, account_name="Nik"))
                    logger.debug("Sent to server: %s", msg)

                else:
                    try:
                        process_message(receive_data(s))
                    except JSONDecodeError as e:
                        logger.error("Json decode error, %s", e)

    except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
        logger.critical("Can't connect to server: %s, %s", (server_port, server_ip), e)

    except Exception as e:
        logger.critical("Something went wrong: %s", e)

    logger.debug("===== End working ===== (main)")


if __name__ == "__main__":
    main()
