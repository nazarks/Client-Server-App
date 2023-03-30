from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QDialog, QPushButton, QTableView

from utils import datetime_from_utc_to_local


class StatWindow(QDialog):
    """
    Класс - окно со статистикой пользователей
    """

    def __init__(self, database):
        super().__init__()

        self.database = database
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle("Статистика клиентов")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнапка закрытия окна
        self.close_button = QPushButton("Закрыть", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с собственно статистикой
        self.stat_table = QTableView(self)
        self.stat_table.move(10, 10)
        self.stat_table.setFixedSize(580, 620)

        self.create_stat_model()

    def create_stat_model(self):
        # Список записей из базы
        hist_list = self.database.get_user_statistic()

        # Объект модели данных:
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(
            ["Имя Клиента", "Последний раз входил", "Сообщений отправлено", "Сообщений получено"]
        )
        for row in hist_list:
            user = QStandardItem(row["name"])
            user.setEditable(False)
            # Дата Время в часовом поясе пользователя
            last_seen = QStandardItem(str(datetime_from_utc_to_local(row["last_login"])))
            last_seen.setEditable(False)
            sent = QStandardItem(str(row["sent_count"]))
            sent.setEditable(False)
            recvd = QStandardItem(str(row["received_count"]))
            recvd.setEditable(False)
            list.appendRow([user, last_seen, sent, recvd])

        self.stat_table.setModel(list)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()
