import argparse
import json
import socket
import time

from settings import DEFAULT_SERVER_PORT, ENCODING_VAR, MAX_DATA_LENGTH


def send_data(connection, data):
    js_message = json.dumps(data)
    connection.send(js_message.encode(ENCODING_VAR))


def recieve_data(connection):
    data = connection.recv(MAX_DATA_LENGTH)
    json_data = json.loads(data.decode(ENCODING_VAR))
    return json_data


def crete_presence(account_name):
    msg = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {"account_name": account_name, "status": "Yep, I am here!"},
    }
    return msg


def process_data(data):
    if "response" in data:
        if data["response"] == 200:
            return "200, OK"
        return f"{data['response']}, {data['error']}"
    return "Can't decode server answer"


def main():
    """
    run client with python3 client.py -h
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="port", type=int, help="Add port please", default=DEFAULT_SERVER_PORT, nargs="?")
    parser.add_argument(dest="server_ip", type=str, help="Add server ip address please")
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        parser.error("Error starting client. The port must be between 1024 and 65535")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.server_ip, args.port))
        msg = crete_presence("Nik")
        send_data(s, msg)
        data = process_data(recieve_data(s))
        print(f"Received: {data}")


if __name__ == "__main__":
    main()
