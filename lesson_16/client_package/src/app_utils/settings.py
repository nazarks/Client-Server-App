# Порт по умолчанию для сетевого взаимодействия
DEFAULT_SERVER_PORT = "7777"

# Адрес для прослушивания сервером, по умолчанию. Если пусто, то слушает все
DEFAULT_SERVER_LISTEN_ADDRESS = ""

# База данных для хранения данных сервера:
SERVER_CONFIG_FILE_NAME = "server.ini"

# IP адрес по умолчанию для подключения клиента
DEFAULT_SERVER_ADDRESS = "127.0.0.1"

# Максимальная очередь подключений
MAX_CONNECTIONS = 5

# Максимальная длинна сообщения в байтах
MAX_DATA_LENGTH = 1024

# Кодировка проекта
ENCODING_VAR = "utf-8"

# Тайм аут сервера
SERVER_TIMEOUT = 0.2

# Путь к серверной базе данных
SERVER_DATABASE = "sqlite:///server_base.db3"

# Путь к клиентской базе данных
CLIENT_DATABASE = "sqlite:///client_base.db3"

# Разрешенные команды для клиента
CLIENT_ALLOWED_COMMAND_LIST = ("msg", "quit", "contacts", "edit", "history")

# Разрешенные команды для сервера
SERVER_CONSOLE_COMMAND_LIST = (
    "users",
    "active_users",
    "login_history",
    "stat",
    "exit",
    "help",
)

# Количество сообщений в чате
MAX_HISTORY_MESSAGES_IN_CHAT = 20
