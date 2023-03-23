DEFAULT_SERVER_PORT = "7777"
DEFAULT_SERVER_LISTEN_ADDRESS = ""
DEFAULT_SERVER_ADDRESS = "127.0.0.1"
MAX_CONNECTIONS = 5
MAX_DATA_LENGTH = 1024
ENCODING_VAR = "utf-8"
SERVER_TIMEOUT = 0.2

SERVER_DATABASE = "sqlite:///server_base.db3"
CLIENT_DATABASE = "sqlite:///client_base.db3"

CLIENT_ALLOWED_COMMAND_LIST = ("msg", "quit", "contacts", "edit", "history")
SERVER_CONSOLE_COMMAND_LIST = ("users", "active_users", "login_history", "stat", "exit", "help")

MAX_ERROR_COUNT = 20
