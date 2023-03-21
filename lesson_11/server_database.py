from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from settings import SERVER_DATABASE

Base = declarative_base()


class ServerStorage:
    # Класс - отображение таблицы всех пользователей
    # Экземпляр этого класса = запись в таблице User
    class User(Base):
        __tablename__ = "user"

        id = Column(Integer, primary_key=True)
        name = Column(String(255), unique=True, nullable=False)
        last_login = Column(DateTime, default=datetime.utcnow, server_default=func.now())

        active_user = relationship("ActiveUser", uselist=False, back_populates="user")
        login_history = relationship("LoginHistory", back_populates="user")

        def __str__(self):
            return f"{self.name} - {self.last_login}"

    # Класс - отображение таблицы активных пользователей:
    # Экземпляр этого класса = запись в таблице ActiveUser
    class ActiveUser(Base):
        __tablename__ = "active_user"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False, unique=True)
        ip_address = Column(String(40), nullable=False)
        port = Column(Integer, nullable=False)
        login_time = Column(DateTime, default=datetime.utcnow, server_default=func.now())

        user = relationship("User", back_populates="active_user")

        def __str__(self):
            return f"{self.user.name} - {self.login_time} - {self.ip_address}:{self.port}"

    # # Класс - отображение таблицы истории входов
    # # Экземпляр этого класса = запись в таблице LoginHistory
    class LoginHistory(Base):
        __tablename__ = "login_history"

        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey("user.id"), nullable=False)
        date_time = Column(DateTime, default=datetime.utcnow, server_default=func.now())
        ip_address = Column(String(40), nullable=False)
        port = Column(Integer, nullable=False)

        user = relationship("User", back_populates="login_history")

        def __str__(self):
            return f"{self.user.name} - {self.date_time} - {self.ip_address}:{self.port}"

    def __init__(self):
        # Создаём движок базы данных
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle - По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось нужно добавить опцию pool_recycle = 7200 (переуст-ка соед-я через 2 часа)
        self.engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
        Base.metadata.create_all(self.engine)

        # Создаём сессию
        Session = sessionmaker(bind=self.engine)  # noqa
        self.session = Session()
        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def data_as_dict(self, data_in_tuple):
        # list tuple - > list dict
        return [dict(data._mapping) for data in data_in_tuple]

    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        user = self.session.query(self.User).filter_by(name=username).one_or_none()
        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if user:
            user.last_login = datetime.utcnow()
        # Если нет, то создаём нового пользователя
        else:
            user = self.User(name=username)
            self.session.add(user)
            # Коммит здесь нужен, чтобы получить ID
            self.session.commit()

        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        new_active_user = self.ActiveUser(user_id=user.id, ip_address=ip_address, port=port)
        self.session.add(new_active_user)

        # и сохранить в историю входов
        # Создаем экземпляр класса LoginHistory, через который передаем данные в таблицу
        history = self.LoginHistory(user_id=user.id, ip_address=ip_address, port=port)
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

    def user_logout(self, username):
        active_user = (
            self.session.query(self.ActiveUser).join(self.ActiveUser.user).filter(self.User.name == username).first()
        )
        self.session.delete(active_user)
        self.session.commit()

    def user_list(self):
        data = self.session.query(self.User.name, self.User.last_login).order_by(self.User.name).all()
        return self.data_as_dict(data)

    def active_users_list(self):
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = (
            self.session.query(
                self.User.name, self.ActiveUser.ip_address, self.ActiveUser.port, self.ActiveUser.login_time
            )
            .join(self.User)
            .order_by(self.ActiveUser.login_time.desc())  # noqa
        )
        # Кортежи в словари
        return self.data_as_dict(query.all())

    # Функция возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        # Запрашиваем историю входа
        query = self.session.query(
            self.User.name, self.LoginHistory.date_time, self.LoginHistory.ip_address, self.LoginHistory.port
        ).join(self.User)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.User.name == username)
        data_from_db = query.order_by(self.LoginHistory.date_time.desc(), self.User.name).all()  # noqa
        return self.data_as_dict(data_from_db)
