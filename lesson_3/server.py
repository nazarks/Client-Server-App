import argparse
import json
import socket
import time

import settings


def send_data(connection, data):
    js_message = json.dumps(data)
    connection.send(js_message.encode(settings.ENCODING_VAR))


def recieve_data(connection):
    data = connection.recv(settings.MAX_DATA_LENGTH)
    json_data = json.loads(data.decode(settings.ENCODING_VAR))
    return json_data


def process_data(data):
    if not ("action" in data and "time" in data and "user" in data):
        return {"response": 400, "time": time.time(), "error": "Bad request."}

    if data["action"] == "presence":
        if data["user"]["account_name"] in settings.USER_LIST:
            return {"response": 200, "time": time.time()}
        else:
            return {"response": 402, "time": time.time(), "error": "No account with that name."}

    return {"response": 400, "time": time.time(), "error": f"{data['action']} Bad action request."}


def main():
    """
    run server with python3 server.py -h

    """
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

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((args.server_listen_ip, args.port))
    server_socket.listen(settings.MAX_CONNECTIONS)
    print("Server is starting...")
    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")
        try:
            # wait for "presence" action
            data = recieve_data(conn)
            print(data)
            response = process_data(data)
            send_data(conn, response)

        except Exception as e:
            print(f"Something went wrong: {e}")
            response = {"response": 400, "time": time.time(), "error": str(e)}
            send_data(conn, response)
        conn.close()


if __name__ == "__main__":
    main()
