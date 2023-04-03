from app_utils.settings import SERVER_CONSOLE_COMMAND_LIST


def print_help():
    print("Поддерживаемые команды:")
    print("users - список известных пользователей")
    print("active_users - список подключенных пользователей")
    print("login_history - история входов пользователя")
    print("stat - статистика пользователя")
    print("exit - завершение работы сервера.")
    print("help - вывод справки по поддерживаемым командам")


def run_server_console_interface(server, database):
    """Функция консольного управления сервером"""
    while True:
        command = input(f"Введите команду {SERVER_CONSOLE_COMMAND_LIST}: ")
        if command == "help":
            print_help()
        elif command == "exit":
            server.close()
            server.thread.join()
            break
        elif command == "users":
            for user in database.user_list():
                print(
                    f"Пользователь {user['name']},"
                    f" последний вход: {user['last_login']}"
                )
        elif command == "active_users":
            for user in database.active_users_list():
                print(
                    f"Пользователь {user['name']},"
                    f" подключен: {user['ip_address']}:{user['port']},"
                    f" время установки соединения: {user['login_time']}"
                )
        elif command == "login_history":
            name = input(
                "Введите имя пользователя для просмотра истории."
                " Для вывода всей истории, просто нажмите Enter: "
            )
            for user in database.login_history(name):
                print(
                    f"Пользователь: {user['name']}"
                    f" время входа: {user['date_time']}."
                    f" Вход с: {user['ip_address']}:{user['port']}"
                )
        elif command == "stat":
            for user in database.get_user_statistic():
                print(
                    f"{user['name']} {user['last_login']}"
                    f" : sent: {user['sent_count']}"
                    f" received: {user['received_count']}"
                )
        else:
            print("Команда не распознана.")
