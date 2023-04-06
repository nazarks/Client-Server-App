from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
)


# Диалог добавление контакта
class AddContactDialog(QDialog):
    """
    Диалог добавления пользователя в список контактов.
    Предлагает пользователю ввести контакт для добавления.
    """

    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle("Привет!")
        self.setFixedSize(275, 93)

        self.label = QLabel("Контакт для добавления:", self)
        self.label.move(10, 10)
        self.label.setFixedSize(250, 10)

        self.contact_name = QLineEdit(self)
        self.contact_name.setFixedSize(254, 20)
        self.contact_name.move(10, 30)

        self.btn_ok = QPushButton("Добавить", self)
        self.btn_ok.move(10, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton("Выход", self)
        self.btn_cancel.move(150, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.show()

    # Обработчик кнопки ОК
    def click(self):
        if self.contact_name.text():
            self.ok_pressed = True


if __name__ == "__main__":
    app = QApplication([])
    dial = AddContactDialog()
    app.exec_()
