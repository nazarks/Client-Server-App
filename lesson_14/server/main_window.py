from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAction, QLabel, QMainWindow, QTableView, qApp

from server.add_user_window import RegisterUser
from server.config_window import ConfigWindow
from server.login_history_window import LoginHistoryWindow
from server.remove_user_window import DelUserDialog
from server.stat_window import StatWindow
from utils import datetime_from_utc_to_local


class MainWindow(QMainWindow):
    """Класс - основное окно сервера."""

    def __init__(self, database, server, config):
        # Конструктор предка
        super().__init__()

        # База данных сервера
        self.database = database

        self.server_thread = server
        self.config = config

        # Ярлык выхода
        self.exitAction = QAction("Выход", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(qApp.quit)

        # Кнопка обновить список клиентов
        self.refresh_button = QAction("Обновить список", self)

        # Кнопка настроек сервера
        self.config_btn = QAction("Настройки сервера", self)

        # Кнопка регистрации пользователя
        self.register_btn = QAction("Регистрация пользователя", self)

        # Кнопка удаления пользователя
        self.remove_btn = QAction("Удаление пользователя", self)

        # Кнопка вывести статистику сообщений
        self.show_stat_button = QAction("Статистика клиентов", self)

        # Кнопка вывести историю подключений
        self.show_login_history_button = QAction("История клиентов", self)

        # Статусбар
        self.statusBar()
        self.statusBar().showMessage("Server Working")

        # Тулбар
        self.toolbar = self.addToolBar("MainBar")
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_stat_button)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)
        self.toolbar.addAction(self.show_login_history_button)
        self.toolbar.addAction(self.config_btn)

        # Настройки геометрии основного окна
        self.setFixedSize(1024, 768)
        self.setWindowTitle("Messaging Server")

        # Надпись о том, что ниже список подключённых клиентов
        self.label = QLabel("Список подключённых клиентов:", self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Таймер, обновляющий список клиентов 1 раз в секунду
        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        # Связываем кнопки с процедурами
        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_stat_button.triggered.connect(self.show_statistics)
        self.show_login_history_button.triggered.connect(self.show_login_history)
        self.config_btn.triggered.connect(self.server_config)

        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.remove_user)

        # Последним параметром отображаем окно.
        self.show()

    def create_users_model(self):
        """Метод заполняющий таблицу активных пользователей."""
        try:
            list_users = self.database.active_users_list()
        except:
            # One session for two thread
            pass
        else:
            list = QStandardItemModel()
            list.setHorizontalHeaderLabels(["Имя Клиента", "IP Адрес", "Порт", "Время подключения"])
            for row in list_users:
                user = QStandardItem(row["name"])
                user.setEditable(False)
                ip = QStandardItem(row["ip_address"])
                ip.setEditable(False)
                port = QStandardItem(str(row["port"]))
                port.setEditable(False)
                # Дата Время в часовом поясе пользователя
                time = QStandardItem(str(datetime_from_utc_to_local(row["login_time"])))
                time.setEditable(False)
                list.appendRow([user, ip, port, time])

            self.active_clients_table.setModel(list)
            self.active_clients_table.resizeColumnsToContents()
            self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Метод создающий окно со статистикой клиентов."""
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def show_login_history(self):
        """Метод создающий окно со статистикой клиентов."""
        global login_history_window
        login_history_window = LoginHistoryWindow(self.database)
        login_history_window.show()

    def server_config(self):
        """Метод создающий окно с настройками сервера."""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """Метод создающий окно регистрации пользователя."""
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def remove_user(self):
        """Метод создающий окно удаления пользователя."""
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()
