import argparse
import json
import logging
import socket
import time

import log.client_log_config
import settings
from log.client_log_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def send_data(connection, data):
    """
    function for sent data to server
    :param connection: connection to server
    :param data: dict
    :return: None
    """
    logger.debug("Running sent_data with params: %s", data)

    js_message = json.dumps(data)
    message = js_message.encode(settings.ENCODING_VAR)
    connection.send(message)


def receive_data(connection):
    """
    receive data from server
    :param
    connection: connection to server
    :return:
    json_data: json
        return json data
    """

    data = connection.recv(settings.MAX_DATA_LENGTH)
    json_data = json.loads(data.decode(settings.ENCODING_VAR))

    logger.debug("Receive data (receive_data): %s", json_data)
    return json_data


def create_presence(account_name):
    """
    :param
    account_name: str
        username for presence message
    :return:
    msg: dict
        return presence message
    """
    logger.debug("Running create_presence with params: %s", account_name)

    msg = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {"account_name": account_name, "status": "Yep, I am here!"},
    }

    return msg


def process_data(data):
    """
    :param
    data: json
        answer from server
    :return: str
        decode answer from server
    """
    logger.debug("Running process_data with params: %s", data)

    if "response" in data:
        if data["response"] == 200:
            return "200, OK"
        return f"{data['response']}, {data['error']}"
    return "Can't decode server answer"


def get_params():
    """
    return params from console
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="port", type=int, help="Add port please", default=settings.DEFAULT_SERVER_PORT, nargs="?")
    parser.add_argument(dest="server_ip", type=str, help="Add server ip address please")
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error("Error starting client. The port must be between 1024 and 65535")

    logger.debug("Args from console %s", args)
    return args.port, args.server_ip


def main():
    """
    run client with python3 client.py -h
    """
    logger.debug("===== Start working ===== (main)")

    server_port, server_ip = get_params()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            msg = create_presence("Nik")
            send_data(s, msg)
            data = process_data(receive_data(s))

            logger.debug("Decoded answer from server (main): %s", data)

    except ConnectionError as e:
        logger.critical("Can't connect to server: %s, %s", (server_port, server_ip), e)

    except Exception as e:
        logger.error("Something went wrong: %s", e)

    logger.debug("===== End working ===== (main)")


if __name__ == "__main__":
    main()
