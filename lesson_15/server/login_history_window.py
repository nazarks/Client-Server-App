from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QPushButton, QTableView

from app_utils.utils import datetime_from_utc_to_local


class LoginHistoryWindow(QDialog):
    """
    Класс окна история подключений пользователей
    """

    def __init__(self, database):
        super().__init__()

        self.database = database
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle("История подключений клиентов")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton("Закрыть", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с собственно историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.create_login_history_model()

    def create_login_history_model(self):
        """Метод заполнения таблицы 'история подключений'"""
        # Список записей из базы
        login_history = self.database.login_history()

        # Объект модели данных:
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ["Имя Клиента", "Дата и Время подключения", "IP Адрес", "Порт"]
        )
        for row in login_history:
            user = QStandardItem(row["name"])
            user.setEditable(False)
            # Дата Время в часовом поясе пользователя
            date_time = QStandardItem(
                str(datetime_from_utc_to_local(row["date_time"]))
            )
            date_time.setEditable(False)
            ip = QStandardItem(row["ip_address"])
            ip.setEditable(False)
            port = QStandardItem(str(row["port"]))
            port.setEditable(False)
            list.appendRow([user, date_time, ip, port])

        self.history_table.setModel(list)
        self.history_table.resizeColumnsToContents()
        self.history_table.resizeRowsToContents()
