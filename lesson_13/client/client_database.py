import sys
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

sys.path.append("../")  # noqa
from settings import CLIENT_DATABASE, MAX_HISTORY_MESSAGES_IN_CHAT

Base = declarative_base()


# Класс - база данных сервера.
class ClientDatabase:
    class Message(Base):
        __tablename__ = "message"

        id = Column(Integer, primary_key=True)
        owner = Column(String(255), nullable=False)
        from_user = Column(String(255), nullable=False)
        to_user = Column(String(255), nullable=False)
        message = Column(Text, nullable=False)
        date_time = Column(DateTime, default=datetime.utcnow, server_default=func.now())

        def __str__(self):
            return f"{self.from_user} - {self.to_user} \n {self.message}"

        # # Класс - отображение списка контактов

    class Contact(Base):
        __tablename__ = "contact"

        id = Column(Integer, primary_key=True)
        owner = Column(String(255), nullable=False)
        contact_name = Column(String(255), nullable=False)

        def __str__(self):
            return f"{self.owner} - {self.contact}"

    # Конструктор класса:
    def __init__(self, owner):
        self.owner = owner
        self.engine = create_engine(
            CLIENT_DATABASE, echo=False, pool_recycle=7200, connect_args={"check_same_thread": False}
        )

        # Создаём объект MetaData
        Base.metadata.create_all(self.engine)

        # Создаём сессию
        Session = sessionmaker(bind=self.engine)  # noqa
        self.session = Session()
        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(self.Contact).filter_by(owner=self.owner).delete()
        self.session.commit()

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contact).filter_by(owner=self.owner, contact_name=contact).first():
            new_contact = self.Contact(owner=self.owner, contact_name=contact)
            self.session.add(new_contact)
            self.session.commit()

    # Функция удаления контакта
    def delete_contact(self, contact):
        self.session.query(self.Contact).filter_by(owner=self.owner, contact_name=contact).delete()
        self.session.commit()

    # Функция сохраняющая сообщения
    def save_message(self, from_user, to_user, message):
        new_message = self.Message(owner=self.owner, from_user=from_user, to_user=to_user, message=message)
        self.session.add(new_message)
        self.session.commit()

    # Функция возвращающая контакты
    def get_contacts(self):
        return [
            contact[0] for contact in self.session.query(self.Contact.contact_name).filter_by(owner=self.owner).all()
        ]

    # Функция проверяющая наличие пользователя контактах
    def check_contact(self, contact):
        if self.session.query(self.Contact).filter_by(owner=self.owner, contact_name=contact).first():
            return True
        else:
            return False

    # Функция возвращающая историю переписки
    def get_messages(self):
        query = self.session.query(self.Message).filter(
            (self.Message.from_user == self.owner) | (self.Message.to_user == self.owner)
        )
        query = query.order_by(self.Message.date_time.desc())
        return [
            (history_row.from_user, history_row.to_user, history_row.message, history_row.date_time)
            for history_row in query.all()
        ]

    def get_messages_by_in_out(self, contact):
        query = self.session.query(self.Message).filter((self.Message.owner == self.owner))
        # query = query.filter((self.Message.from_user == self.owner) | (self.Message.to_user == self.owner))
        query = query.filter((self.Message.from_user == contact) | (self.Message.to_user == contact))
        query = query.order_by(self.Message.date_time.desc())
        messages = [
            [history_row.from_user, history_row.to_user, history_row.message, history_row.date_time]
            for history_row in query.limit(MAX_HISTORY_MESSAGES_IN_CHAT).all()[::-1]
        ]
        for message in messages:
            if message[0] == self.owner:
                message.append("out")
            else:
                message.append("in")

        return messages


# отладка
if __name__ == "__main__":
    pass
    test_db = ClientDatabase(owner="user1")
    for cnt in ["test3", "test4", "test5"]:
        test_db.add_contact(contact=cnt)
    print("Contact list")
    print(test_db.get_contacts())
    test_db.add_contact(contact="test4")
    test_db.add_contact(contact="test4")
    print("Contact list from ")
    print(test_db.get_contacts())
    test_db.save_message(
        from_user="user1",
        to_user="user2",
        message=f"Привет! я тестовое сообщение 1 от {datetime.now()}!",
    )
    test_db.save_message(
        from_user="user2",
        to_user="user1",
        message=f"Привет! я тестовое сообщение 2 от {datetime.now()}!",
    )
    print(test_db.get_messages())
    print("Contact test1 delete: ", test_db.delete_contact(contact="test1"))
    print("Contact test3 delete: ", test_db.delete_contact(contact="test3"))
    print("Contact list from ")
    print(test_db.get_contacts())
