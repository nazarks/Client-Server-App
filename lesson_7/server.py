import argparse
import json
import logging
import socket
import time
import select
from json import JSONDecodeError

import log.server_log_config
import settings
from log.server_log_config import LOGGER_NAME
from utils import FunctionLog

logger = logging.getLogger(LOGGER_NAME)


def get_client_description(sock):
    """
    get client description
    :param sock: socket
    :return: str
    """
    try:
        return f"Client id: {sock.fileno()}, {sock.getpeername()}"
    except OSError:
        # client offline, no transport parameters
        return f"Client id: {sock.fileno()}"


@FunctionLog(logger)
def process_requests(r_clients, all_clients):
    """
    read ready clients
    :param r_clients:list список клиентов готовых к чтению
    :param all_clients:list список все клиентов
    :return: messages:list список сообщений вида [{"from": имя клиента}, {"message": сообщение},]
    """
    messages_list = []

    for sock in r_clients:
        try:
            data = receive_data(sock)
            print("receive_data", data)

            if data:
                process_client_message(sock, data, messages_list)
                print("messages_list", messages_list)
                logger.debug("Get request from %s, data: %s", get_client_description(sock), data)
        except Exception as e:
            print(e)
            logger.debug(
                "Function process_requests: client disconnected, %s. Removed from client list",
                get_client_description(sock),
            )
            all_clients.remove(sock)
    return messages_list


@FunctionLog(logger)
def process_client_message(sock, message, message_list):
    """

    :param sock: socket connection
    :param message: str message
    :param message_list: list[dict,]
    :return:
    """
    if "action" in message and message["action"] == "presence" and "time" in message and "user" in message:
        if message["user"]["account_name"] in settings.USER_LIST:
            # if message type presence return answer
            send_data(sock, {"response": 200, "time": time.time()})
            return
        else:
            # user not found, return answer
            send_data(sock, {"response": 402, "time": time.time(), "error": "No account with that name."})
            return

    if (
        "action" in message
        and message["action"] == "msg"
        and "time" in message
        and "message" in message
        and "from" in message
    ):
        # new message add to message list
        message_list.append({"from": message["from"], "message": message["message"]})
        return

    # can't decode message
    send_data(
        sock,
        {
            "response": 400,
            "time": time.time(),
            "error": "Bad request.",
        },
    )


@FunctionLog(logger)
def write_responses(messages_list, w_clients, all_clients):
    """
    sent message to waiting clients
    :param messages_list:list список ответов
    :param w_clients: список клиентов готовых к ответу
    :param all_clients: список всех активных клиентов
    :return:None
    """

    for message in messages_list:
        message_dict = {
            "action": "msg",
            "time": time.time(),
            "from": message["from"],
            "message": message["message"],
        }
        for sock in w_clients:
            try:
                send_data(sock, message_dict)

                logger.debug("Sent response to %s, data: %s", get_client_description(sock), message_dict)
            except:
                logger.debug("Client disconnected: %s. Removed from activ client list", get_client_description(sock))
                sock.close()
                all_clients.remove(sock)


@FunctionLog(logger)
def send_data(sock, data):
    js_message = json.dumps(data)
    message = js_message.encode(settings.ENCODING_VAR)

    sock.send(message)


@FunctionLog(logger)
def receive_data(sock):
    try:
        data = sock.recv(settings.MAX_DATA_LENGTH)
        print("receive_data", data)
        json_data = json.loads(data.decode(settings.ENCODING_VAR))
    except JSONDecodeError:
        return "NonJsonMessage"
    return json_data


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


@FunctionLog(logger)
def get_server_socket():
    try:
        server_port, server_listen_ip = get_params()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_listen_ip, server_port))
        server_socket.listen(settings.MAX_CONNECTIONS)
        server_socket.settimeout(settings.SERVER_TIMEOUT)
        logger.debug("Server with params %s,  is starting...", server_socket.getsockname())

    except Exception as e:
        logger.critical("Error starting server %s", e)
        raise Exception(f"Error starting server {e}")

    return server_socket


def main():
    """
    run server with python3 server.py -h

    """
    logger.debug("===== Start working ===== (main)")

    clients = []
    server_socket = get_server_socket()

    while True:
        messages_list = []
        try:
            # Проверка подключений
            conn, addr = server_socket.accept()
        except OSError:
            # Никто не подключился
            pass
        else:
            logger.debug("Connect from client accepted: %s", get_client_description(conn))
            clients.append(conn)
        finally:
            # Проверить наличие событий ввода вывода
            wait = 1
            ready_to_read_clients = []
            ready_to_write_clients = []
            try:
                ready_to_read_clients, ready_to_write_clients, clients_with_errors = select.select(
                    clients,
                    clients,
                    [],
                    wait,
                )
            except OSError:
                # Ничего не делать, если какой-то клиент отключился
                pass

            if ready_to_read_clients:
                messages_list = process_requests(ready_to_read_clients, clients)
            if messages_list and ready_to_write_clients:
                write_responses(messages_list, ready_to_write_clients, clients)


if __name__ == "__main__":
    main()
