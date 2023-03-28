import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableView,
    qApp,
)

from utils import datetime_from_utc_to_local


# GUI - Создание таблицы QModel, для отображения в окне программы (active_users).
def create_active_users_model(database):
    list_users = database.active_users_list()
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
    return list


# GUI - Функция реализующая заполнение таблицы статистики клиентов.
def create_stat_model(database):
    # Список записей из базы
    hist_list = database.get_user_statistic()

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
    return list


# GUI - Функция реализующая заполнение таблицы история входов клиентов.
def create_login_history_model(database):
    # Список записей из базы
    login_history = database.login_history()
    print(login_history)
    # Объект модели данных:
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(["Имя Клиента", "Дата и Время подключения", "IP Адрес", "Порт"])
    for row in login_history:
        user = QStandardItem(row["name"])
        user.setEditable(False)
        # Дата Время в часовом поясе пользователя
        date_time = QStandardItem(str(datetime_from_utc_to_local(row["date_time"])))
        date_time.setEditable(False)
        ip = QStandardItem(row["ip_address"])
        ip.setEditable(False)
        port = QStandardItem(str(row["port"]))
        port.setEditable(False)
        list.appendRow([user, date_time, ip, port])
    return list


# Класс основного окна
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Кнопка выхода
        exitAction = QAction("Выход", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(qApp.quit)

        # Кнопка обновить список клиентов
        self.refresh_button = QAction("Обновить список", self)

        # Кнопка настроек сервера
        self.config_btn = QAction("Настройки сервера", self)

        # Кнопка вывести статистику
        self.show_stat_button = QAction("Статистика клиентов", self)

        # Кнопка вывести историю подключений
        self.show_login_history_button = QAction("История клиентов", self)

        # Статусбар
        # dock widget
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar("MainBar")
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_stat_button)
        self.toolbar.addAction(self.show_login_history_button)
        self.toolbar.addAction(self.config_btn)

        # Настройки геометрии основного окна
        self.setFixedSize(800, 600)
        self.setWindowTitle("Messaging Server")

        # Надпись о том, что ниже список подключённых клиентов
        self.label = QLabel("Список подключённых клиентов:", self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        # Последним параметром отображаем окно.
        self.show()


# Класс окна статистика пользователей
class StatWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle("Статистика клиентов")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton("Закрыть", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист статистики
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


# Класс окна история подключений пользователей
class LoginHistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
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

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(640, 480)
        self.setWindowTitle("Настройки сервера")

        # Надпись о файле базы данных:
        self.db_path_label = QLabel("Путь до файла базы данных: ", self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(400, 15)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(400, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton("Обзор...", self)
        self.db_path_select.move(420, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace("/", "\\")
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel("Имя файла базы данных: ", self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(400, 66)
        self.db_file.setFixedSize(150, 20)

        # Метка с номером порта
        self.port_label = QLabel("Номер порта для соединений:", self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(400, 108)
        self.port.setFixedSize(150, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel("С какого IP принимаем соединения:", self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(280, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel("Оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.", self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(400, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton("Сохранить", self)
        self.save_btn.move(190, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton("Закрыть", self)
        self.close_button.move(300, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.statusBar().showMessage("Test Statusbar Message")
    test_list = QStandardItemModel(ex)
    test_list.setHorizontalHeaderLabels(["Имя Клиента", "IP Адрес", "Порт", "Время подключения"])
    test_list.appendRow([QStandardItem("1"), QStandardItem("2"), QStandardItem("3")])
    test_list.appendRow([QStandardItem("4"), QStandardItem("5"), QStandardItem("6")])
    ex.active_clients_table.setModel(test_list)
    ex.active_clients_table.resizeColumnsToContents()
    app.exec_()
    # app = QApplication(sys.argv)
    # message = QMessageBox
    # dial = ConfigWindow()
    #
    # app.exec_()
