from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    qApp,
)


# Стартовый диалог с выбором имени пользователя
class UserNameDialog(QDialog):
    """
    Класс реализующий стартовый диалог с запросом логина
    и пароля пользователя.
    """

    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle("Привет!")
        self.setFixedSize(300, 150)

        self.label = QLabel("Введите имя пользователя:", self)
        self.label.move(10, 10)
        self.label.setFixedSize(200, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(250, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel("Введите пароль:", self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(250, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton("Начать", self)
        self.btn_ok.move(30, 110)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton("Выход", self)
        self.btn_cancel.move(140, 110)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    # Обработчик кнопки ОК, если поле вводе не пустое,
    # ставим флаг и завершаем приложение.
    def click(self):
        """Метод обработчик кнопки ОК."""
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == "__main__":
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
