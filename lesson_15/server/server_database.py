import logging
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

import log.server_log_config  # noqa
from log.server_log_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

Base = declarative_base()


class ServerStorage:
    """
    Класс - оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется декларативный подход.
    """

    class User(Base):
        """
        Класс - отображение таблицы всех пользователей
        Экземпляр этого класса = запись в таблице User
        """

        __tablename__ = "user"

        id = Column(Integer, primary_key=True)
        name = Column(String(255), unique=True, nullable=False)
        last_login = Column(
            DateTime, default=datetime.utcnow, server_default=func.now()
        )
        passwd_hash = Column(String(255), nullable=False)

        active_user = relationship(
            "ActiveUser", uselist=False, back_populates="user"
        )
        login_history = relationship("LoginHistory", back_populates="user")
        statistic = relationship("UserStatistic", back_populates="user")

        def __str__(self):
            return f"{self.name} - {self.last_login}"

    class ActiveUser(Base):
        """
        Класс - отображение таблицы активных пользователей:
        Экземпляр этого класса = запись в таблице ActiveUser
        """

        __tablename__ = "active_user"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False, unique=True)
        ip_address = Column(String(40), nullable=False)
        port = Column(Integer, nullable=False)
        login_time = Column(
            DateTime, default=datetime.utcnow, server_default=func.now()
        )

        user = relationship("User", back_populates="active_user")

        def __str__(self):
            return (
                f"{self.user.name} - {self.login_time}"
                f" - {self.ip_address}:{self.port}"
            )

    class LoginHistory(Base):
        """
        Класс - отображение таблицы истории входов
        Экземпляр этого класса = запись в таблице LoginHistory
        """

        __tablename__ = "login_history"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False)
        date_time = Column(
            DateTime, default=datetime.utcnow, server_default=func.now()
        )
        ip_address = Column(String(40), nullable=False)
        port = Column(Integer, nullable=False)

        user = relationship("User", back_populates="login_history")

        def __str__(self):
            return (
                f"{self.user.name} - {self.date_time} "
                f"- {self.ip_address}:{self.port}"
            )

    class UserContact(Base):
        """
        Класс - отображение таблицы контактов пользователей.
        """

        __tablename__ = "user_contact"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False)
        date_time = Column(
            DateTime, default=datetime.utcnow, server_default=func.now()
        )
        contact_id = Column(ForeignKey("user.id"), nullable=False)

        user = relationship("User", foreign_keys=[user_id])
        contact = relationship("User", foreign_keys=[contact_id])

        def __str__(self):
            return f"{self.user.name} - {self.contact.name}"

    class UserStatistic(Base):
        """
        Класс - отображение таблицы статистики.
        """

        __tablename__ = "user_statistic"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False)
        sent_count = Column(Integer, default=0)
        received_count = Column(Integer, default=0)

        user = relationship("User", back_populates="statistic")

        def __str__(self):
            return (
                f"{self.user.name} - Sent: {self.sent_count}"
                f" - Accepted: {self.received_count}"
            )

    def __init__(self, path):
        # Создаём движок базы данных
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle -
        # По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось нужно добавить опцию
        # pool_recycle = 7200 (переуст-ка соед-я через 2 часа)
        self.engine = create_engine(
            f"sqlite:///{path}",
            echo=False,
            pool_recycle=7200,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)

        # Создаём сессию
        Session = sessionmaker(bind=self.engine)  # noqa
        self.session = Session()
        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def data_as_dict(self, data_in_tuple):
        """
        Метод конвертации списка в словарь, использую данные ответа из query
        """
        return [dict(data._mapping) for data in data_in_tuple]

    def user_login(self, username, ip_address, port):
        """
        Метод выполняющийся при входе пользователя,
        записывает в базу факт входа.
        Обновляет открытый ключ пользователя при его изменении.
        """

        # Запрос в таблицу пользователей на наличие
        # там пользователя с таким именем
        user = (
            self.session.query(self.User)
            .filter_by(name=username)
            .one_or_none()
        )
        # Если имя пользователя уже присутствует в таблице,
        # обновляем время последнего входа
        if user:
            user.last_login = datetime.utcnow()
        # Если нет, то ошибка
        else:
            raise ValueError(f"User not exist {username}")

        # Теперь можно создать запись в таблицу активных пользователей
        # о факте входа.
        new_active_user = self.ActiveUser(
            user_id=user.id, ip_address=ip_address, port=port
        )
        self.session.add(new_active_user)

        # и сохранить в историю входов.
        # Создаем экземпляр класса LoginHistory,
        # через который передаем данные в таблицу
        history = self.LoginHistory(
            user_id=user.id, ip_address=ip_address, port=port
        )
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

    def add_update_user(self, username, passwd_hash):
        """
        Метод добавляем или пользователя или обновления ему пароля,
        функция администратора
        """
        user = (
            self.session.query(self.User)
            .filter_by(name=username)
            .one_or_none()
        )
        # Если имя пользователя уже присутствует в таблице, обновляем пароль
        if user:
            user.passwd_hash = passwd_hash
        # Если нет, то создаём нового пользователя
        else:
            user = self.User(name=username, passwd_hash=passwd_hash)
            self.session.add(user)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.User).filter_by(name=name).first()
        self.session.query(self.ActiveUser).filter_by(user_id=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(
            user_id=user.id
        ).delete()
        self.session.query(self.UserContact).filter_by(
            user_id=user.id
        ).delete()
        self.session.query(self.UserContact).filter_by(
            contact_id=user.id
        ).delete()
        self.session.query(self.UserStatistic).filter_by(
            user_id=user.id
        ).delete()
        self.session.query(self.User).filter_by(name=name).delete()
        self.session.commit()

    def user_exists(self, username):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.User).filter_by(name=username).first():
            return True
        return False

    def user_logout(self, username):
        """Метод фиксирующий отключения пользователя."""
        active_user = (
            self.session.query(self.ActiveUser)
            .join(self.ActiveUser.user)
            .filter(self.User.name == username)
            .first()
        )
        self.session.delete(active_user)
        self.session.commit()

    def user_list(self):
        """Метод получения списка пользователя"""
        data = (
            self.session.query(self.User.name, self.User.last_login)
            .order_by(self.User.name)
            .all()
        )
        return self.data_as_dict(data)

    def active_users_list(self):
        """Метод получения активных пользователей"""
        # Запрашиваем соединение таблиц
        # и собираем кортежи имя, адрес, порт, время.
        query = (
            self.session.query(
                self.User.name,
                self.ActiveUser.ip_address,
                self.ActiveUser.port,
                self.ActiveUser.login_time,
            )
            .join(self.User)
            .order_by(self.ActiveUser.login_time.desc())  # noqa
        )
        # Кортежи в словари
        return self.data_as_dict(query.all())

    def login_history(self, username=None):
        """
        Функция возвращающая историю входов
        по пользователю или всем пользователям
        """

        # Запрашиваем историю входа
        query = self.session.query(
            self.User.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip_address,
            self.LoginHistory.port,
        ).join(self.User)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.User.name == username)
        data_from_db = query.order_by(
            self.LoginHistory.date_time.desc(), self.User.name
        ).all()  # noqa
        return self.data_as_dict(data_from_db)

    def add_contact(self, user_name, contact_name):
        """Метод добавления контакта для пользователя."""
        user = (
            self.session.query(self.User)
            .filter(self.User.name == user_name)
            .one()
        )
        user_for_contact = (
            self.session.query(self.User)
            .filter(self.User.name == contact_name)
            .one_or_none()
        )
        if not user_for_contact:
            raise SQLAlchemyError("Contact not in user list")
        contact_exists = (
            self.session.query(self.UserContact)
            .filter_by(user_id=user.id, contact_id=user_for_contact.id)
            .one_or_none()
        )
        if contact_exists:
            raise SQLAlchemyError("Contact already exists")
        new_user_contact = self.UserContact(
            user_id=user.id, contact_id=user_for_contact.id
        )
        self.session.add(new_user_contact)
        self.session.commit()
        logger.debug(f"New contact added successfully {new_user_contact}")

    def delete_contact(self, user_name, contact_name):
        """Метод удаления контакта пользователя."""
        user = (
            self.session.query(self.User)
            .filter(self.User.name == user_name)
            .one()
        )
        user_for_contact = (
            self.session.query(self.User)
            .filter(self.User.name == contact_name)
            .one_or_none()
        )

        if not user_for_contact:
            raise SQLAlchemyError("Contact not in user list")
        self.session.query(self.UserContact).filter_by(
            user_id=user.id, contact_id=user_for_contact.id
        ).delete()
        self.session.commit()

    def get_user_contacts(self, username):
        """Метод возвращает список контактов пользователя."""
        # id пользователя
        user = self.session.query(self.User).filter_by(name=username).one()
        # Запрашиваем его список контактов
        query = (
            self.session.query(self.UserContact.user_id, self.User.name)
            .filter_by(user_id=user.id)
            .join(self.UserContact.contact)
        )

        return [contact[1] for contact in query.all()]

    def update_user_statistic(self, from_user, to_user):
        """Метод обновляющий статистику сообщений пользователя"""
        # Если пользователь отправил сообщение самому себе,
        # то статистику не меняем
        if from_user == to_user:
            return

        # Ищем статистику по отправленным сообщениям
        user_sender = (
            self.session.query(self.UserStatistic)
            .join(self.UserStatistic.user)
            .filter(self.User.name == from_user)
            .one_or_none()
        )
        # Если статистика есть, обновляем
        if user_sender:
            user_sender.sent_count += 1
        else:
            # Если нет создаем запись
            user = (
                self.session.query(self.User)
                .filter(self.User.name == from_user)
                .one()
            )
            user_sender = self.UserStatistic(user_id=user.id, sent_count=1)
            self.session.add(user_sender)

        # Ищем статистику по полученным сообщениям

        user_recipient = (
            self.session.query(self.UserStatistic)
            .join(self.UserStatistic.user)
            .filter(self.User.name == to_user)
            .one_or_none()
        )

        # Если статистика есть, обновляем
        if user_recipient:
            user_recipient.received_count += 1
        else:
            # Если нет создаем запись
            user = (
                self.session.query(self.User)
                .filter(self.User.name == to_user)
                .one()
            )
            user_recipient = self.UserStatistic(
                user_id=user.id, received_count=1
            )
            self.session.add(user_recipient)

        self.session.commit()

    def get_user_statistic(self):
        """Метод получающий статистику всех пользователе"""
        query = self.session.query(
            self.User.name,
            self.User.last_login,
            self.UserStatistic.sent_count,
            self.UserStatistic.received_count,
        ).join(self.User)
        return self.data_as_dict(query.all())

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        passwd_hash = (
            self.session.query(self.User.passwd_hash)
            .filter_by(name=name)
            .first()
        )
        return passwd_hash[0]


if __name__ == "__main__":
    pass
