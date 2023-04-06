import logging

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMainWindow, QMessageBox, qApp

from app_utils.errors import ServerError
from app_utils.utils import datetime_from_utc_to_local

# sys.path.append("../")
from client.add_contact_dialog import AddContactDialog
from client.del_contact import DelContactDialog
from client.main_window_conv import Ui_MainClientWindow

logger = logging.getLogger("client")


# Класс основного окна
class ClientMainWindow(QMainWindow):
    """
    Класс - основное окно пользователя.
    Содержит всю основную логику работы клиентского модуля.
    Конфигурация окна загружается из файла main_window_conv.py
    """

    def __init__(self, database, transport):
        super().__init__()
        # основные переменные
        self.database = database
        self.transport = transport

        # Загружаем конфигурацию окна из дизайнера
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # Кнопка "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    # Деактивировать поля ввода
    def set_disabled_input(self):
        """Метод делающий поля ввода неактивными"""

        # Надпись  - получатель.
        self.ui.label_new_message.setText(
            "Для выбора получателя дважды кликните на нем в окне контактов."
        )
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    # Заполняем историю сообщений.
    def history_list_update(self):
        """
        Метод заполняющий соответствующий QListView
        историей переписки с текущим собеседником.
        """

        # Получаем историю, сортированную по дате
        messages = self.database.get_messages_by_in_out(
            contact=self.current_chat
        )
        logger.debug(
            "history_list_update %s for user %s",
            str(messages),
            self.transport.username,
        )
        # Если модель не создана, создадим.
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        for message in messages:
            if message[4] == "in":
                mess = QStandardItem(
                    f"Входящее от"
                    f" {datetime_from_utc_to_local(message[3])}:\n {message[2]}"
                )
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(
                    f"Исходящее от"
                    f" {datetime_from_utc_to_local(message[3])}:\n {message[2]}"
                )
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Функция обработчик даблклика по контакту
    def select_active_user(self):
        """Метод обработчик события двойного клика по списку контактов."""
        # Выбранный пользователем (даблклик)
        # находится в выделенном элементе в QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # вызываем основную функцию
        self.set_active_user()

    # Функция устанавливающая активного собеседника
    def set_active_user(self):
        """Метод активации чата с собеседником."""
        # Ставим надпись и активируем кнопки
        self.ui.label_new_message.setText(
            f"Введите сообщение для {self.current_chat}:"
        )
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    # Функция обновляющая контакт лист
    def clients_list_update(self):
        """Метод обновляющий список контактов."""
        contacts_list = self.database.get_contacts()
        logger.debug("Contact_list update: %s", str(contacts_list))
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # Функция добавления контакта
    def add_contact_window(self):
        """Метод создающий окно - диалог добавления контакта"""
        add_contact_dialog = AddContactDialog()
        add_contact_dialog.btn_ok.clicked.connect(
            lambda: self.add_contact_action(add_contact_dialog)
        )
        add_contact_dialog.show()

    # Функция - обработчик добавления контакта
    def add_contact_action(self, item):
        """Метод обработчик нажатия кнопки 'Добавить'"""
        new_contact = item.contact_name.text()
        print(new_contact)
        if item.ok_pressed:
            self.add_contact(new_contact)
        item.close()

    # Функция добавляющая контакт в базы
    def add_contact(self, new_contact):
        """
        Метод добавляющий контакт в серверную и клиентскую BD.
        После обновления баз данных обновляет и содержимое окна.
        """

        try:
            self.transport.add_contact(new_contact)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, "Ошибка", "Потеряно соединение с сервером!"
                )
                self.close()
            # Таймаут освобождения сокета
            self.messages.critical(self, "Ошибка", "Таймаут соединения!")
        except ServerError as err:
            self.messages.critical(self, "Ошибка сервера", str(err))
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f"Успешно добавлен контакт {new_contact}")
            self.messages.information(
                self, "Успех", "Контакт успешно добавлен."
            )

    # Функция удаления контакта
    def delete_contact_window(self):
        """Метод создающий окно удаления контакта."""
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(
            lambda: self.delete_contact(remove_dialog)
        )
        remove_dialog.show()

    # Функция обработчик удаления контакта,
    # сообщает на сервер, обновляет таблицу контактов
    def delete_contact(self, item):
        """
        Метод удаляющий контакт из серверной и клиентской BD.
        После обновления баз данных обновляет и содержимое окна.
        """

        selected = item.selector.currentText()
        try:
            self.transport.delete_contact(selected)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, "Ошибка", "Потеряно соединение с сервером!"
                )
                self.close()
            # Таймаут пропуск
            # self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except ServerError as err:
            self.messages.critical(self, "Ошибка сервера", str(err))
        else:
            self.database.delete_contact(selected)
            self.clients_list_update()
            logger.info(f"Успешно удалён контакт {selected}")
            self.messages.information(
                self,
                "Успех",
                "Контакт" " успешно удалён.",
            )
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """Функция отправки сообщения текущему собеседнику."""
        # Текст в поле, проверяем что поле не пустое
        # затем забирается сообщение и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.transport.settimeout(1)
            self.transport.sent_message_to_user(
                msg=message_text, to_user=self.current_chat
            )
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, "Ошибка", "Потеряно соединение с сервером!"
                )
                self.close()
            else:
                # Освобождаем сокет по Timeout,
                # сервер не вернул ошибок значит все хорошо

                self.database.save_message(
                    from_user=self.transport.username,
                    to_user=self.current_chat,
                    message=message_text,
                )
                logger.debug(
                    f"Отправлено сообщение для"
                    f" {self.current_chat}: {message_text}"
                )
                self.history_list_update()

        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(
                self, "Ошибка", "Потеряно соединение с сервером!"
            )
            self.close()
        except ServerError as err:
            self.messages.critical(self, "Ошибка", str(err))
        else:
            self.database.save_message(
                from_user=self.transport.username,
                to_user=self.current_chat,
                message=message_text,
            )
            logger.debug(
                f"Отправлено сообщение для"
                f" {self.current_chat}: {message_text}"
            )
            self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(str)
    def message(self, sender):
        """
        Слот обработчик поступаемый сообщений.
        Запрашивает пользователя если пришло
        сообщение не от текущего собеседника.
        При необходимости меняет собеседника.
        """
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                # Если есть, спрашиваем и желании
                # открыть с ним чат и открываем при желании
                if (
                    self.messages.question(
                        self,
                        "Новое сообщение",
                        f"Получено новое сообщение от {sender},"
                        f" открыть чат с ним?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print("NO")
                # Раз нет, спрашиваем хотим ли добавить юзера в контакты.
                if (
                    self.messages.question(
                        self,
                        "Новое сообщение",
                        f"Получено новое сообщение от {sender}.\n"
                        f" Данного пользователя нет в вашем контакт-листе.\n"
                        f" Добавить в контакты и открыть чат с ним?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    # Слот потери соединения
    # Выдаёт сообщение об ошибке и завершает работу приложения
    @pyqtSlot()
    def connection_lost(self):
        """
        Слот обработчик потери соединения с сервером.
        Выдаёт окно предупреждение и завершает работу приложения.
        """

        self.messages.critical(
            self, "Сбой соединения", "Потеряно соединение с сервером. "
        )
        self.close()

    def make_connection(self, trans_obj):
        """Метод обеспечивающий соединение сигналов и слотов."""
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
