import argparse
import json
import socket
import time

import settings


def send_data(connection, data):
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

    return args.port, args.server_ip


def main():
    """
    run client with python3 client.py -h
    """
    server_port, server_ip = get_params()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        msg = create_presence("Nik")
        send_data(s, msg)
        data = process_data(receive_data(s))
        print(f"Received: {data}")


if __name__ == "__main__":
    main()
