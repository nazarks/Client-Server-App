import json
import os
import sys
from unittest import TestCase, main, mock

sys.path.append(os.path.join(os.getcwd(), ".."))

from client import create_presence, get_params, process_data, receive_data, send_data  # noqa: E402
from settings import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, ENCODING_VAR  # noqa: E402


class SocketHandler:
    def __init__(self):
        fixed_time = 1000
        client_data = {
            "action": "presence",
            "time": fixed_time,
            "type": "status",
            "user": {"account_name": "Nik", "status": "Yep, I am here!"},
        }
        msg = json.dumps(client_data)
        msg = msg.encode(ENCODING_VAR)

        self.sent_data = None
        self.received_data = msg
        self.client_data = client_data

    def send(self, message):
        self.sent_data = message

    def recv(self, max_length):
        return self.received_data


mock_socket = SocketHandler()


class TestClient(TestCase):
    def test_create_presence(self):
        fixed_time = 1000
        msg = {
            "action": "presence",
            "time": fixed_time,
            "type": "status",
            "user": {"account_name": "Nik", "status": "Yep, I am here!"},
        }
        answer = create_presence("Nik")
        answer["time"] = fixed_time
        self.assertEqual(answer, msg), "Wrong presence"

    def test_process_data_ok(self):
        fixed_time = 1000
        input_string = {"response": 200, "time": fixed_time}
        answer = process_data(input_string)
        self.assertEqual(answer, "200, OK")

    def test_process_data_402(self):
        fixed_time = 1000
        input_string = {"response": 402, "time": fixed_time, "error": "No account with that name."}
        answer = process_data(input_string)
        self.assertEqual(answer, "402, No account with that name.")

    def test_get_params_default_port(self):
        with mock.patch("argparse._sys.argv", ["", DEFAULT_SERVER_ADDRESS]):
            params = get_params()
        self.assertEqual((int(DEFAULT_SERVER_PORT), DEFAULT_SERVER_ADDRESS), params)

    def test_get_params_ok(self):
        new_port = "9999"
        new_server_ip = "192.168.1.100"
        sys.argv.append(new_port)
        sys.argv.append(new_server_ip)

        params = get_params()
        self.assertEqual((int(new_port), new_server_ip), params)

    def test_get_params_bad(self):
        with self.assertRaises(SystemExit) as cm:
            get_params()
        self.assertEqual(cm.exception.code, 2)

    def test_send_data_ok(self):
        client_data = mock_socket.client_data

        send_data(mock_socket, client_data)
        self.assertEqual(mock_socket.sent_data, mock_socket.received_data)

    def test_received_data_ok(self):
        data = receive_data(mock_socket)
        self.assertEqual(data, mock_socket.client_data)


if __name__ == "__main__":
    main()
