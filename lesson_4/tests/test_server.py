import json
import os
import sys
from unittest import TestCase, main

sys.path.append(os.path.join(os.getcwd(), ".."))

from server import get_params, process_data, receive_data, send_data  # noqa: E402
from settings import DEFAULT_SERVER_LISTEN_ADDRESS, DEFAULT_SERVER_PORT, ENCODING_VAR  # noqa: E402


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
    fixed_time = 1000
    msg = {
        "action": "presence",
        "time": fixed_time,
        "type": "status",
        "user": {"account_name": "Nik", "status": "Yep, I am here!"},
    }

    def test_process_data_ok(self):
        """
        :return:
        # return {"response": 200, "time": time.time()}
        """
        answer = process_data(self.msg)
        answer["time"] = self.fixed_time
        self.assertEqual(answer, {"response": 200, "time": self.fixed_time})

    def test_process_data_bad_action_request(self):
        """
        :return:
            # {"response": 400, "time": time.time(), "error": f"{data['action']} Bad action request."}
        """
        bad_msg = {
            "action": "bad_presence",
            "time": self.fixed_time,
            "type": "status",
            "user": {"account_name": "Nik", "status": "Yep, I am here!"},
        }
        answer = process_data(bad_msg)
        answer["time"] = self.fixed_time
        self.assertEqual(
            answer,
            {
                "response": 400,
                "time": self.fixed_time,
                "error": "bad_presence Bad action request.",
            },
        )

    def test_process_data_bad_request(self):
        """
        :return:
        #  return {"response": 400, "time": time.time(), "error": "Bad request."}
        """
        bad_msg = {
            "bad_action": "presence",
            "time": self.fixed_time,
            "type": "status",
            "user": {"account_name": "Nik", "status": "Yep, I am here!"},
        }
        answer = process_data(bad_msg)
        answer["time"] = self.fixed_time
        self.assertEqual(answer, {"response": 400, "time": self.fixed_time, "error": "Bad request."})

    def test_process_data_bad_account(self):
        """
        :return:
        # return {"response": 402, "time": time.time(), "error": "No account with that name."}
        """
        bad_msg = {
            "action": "presence",
            "time": self.fixed_time,
            "type": "status",
            "user": {"account_name": "NoName", "status": "Yep, I am here!"},
        }
        answer = process_data(bad_msg)
        answer["time"] = self.fixed_time
        self.assertEqual(answer, {"response": 402, "time": self.fixed_time, "error": "No account with that name."})

    def test_get_params_default_ok(self):
        """
        :return:
            # port, server_listen_ip
        """
        params = get_params()
        self.assertEqual((int(DEFAULT_SERVER_PORT), DEFAULT_SERVER_LISTEN_ADDRESS), params)

    def test_get_params_ok(self):
        """
        :return:
            # port, server_listen_ip
        """
        sys.argv[1:] = ["-p", "9999", "-a", "192.168.0.1"]
        params = get_params()
        self.assertEqual((9999, "192.168.0.1"), params)

    def test_send_data_ok(self):
        fixed_time = 1000
        input_string = {"response": 200, "time": fixed_time}
        send_data(mock_socket, input_string)

        self.assertEqual(mock_socket.sent_data, b'{"response": 200, "time": 1000}')

    def test_receive_data_ok(self):
        data = receive_data(mock_socket)
        input_json = mock_socket.client_data
        self.assertEqual(data, input_json)


if __name__ == "__main__":
    main()
