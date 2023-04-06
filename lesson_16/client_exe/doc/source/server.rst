server module
=============

Серверный модуль мессенджера. Обрабатывает словари - сообщения.

Использование

Модуль подерживает аргементы командной стороки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.

* В данном режиме поддерживается только 1 команда: exit - завершение работы.
* Есть выбор между консольной или GUI версией

Примеры использования:

``python server.py -p 8080``

*Запуск сервера на порту 8080*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*


server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 2 элементов:

    * адрес с которого принимать соединения
    * порт

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

core.py
~~~~~~~~~~~

.. autoclass:: server.core.ServerCore
    :members:

server_database.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: server.server_database.ServerStorage
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: server.main_window.MainWindow
    :members:

add_user_window.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: server.add_user_window.RegisterUser
    :members:

remove_user_window.py
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.remove_user_window.DelUserDialog
    :members:

config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.config_window.ConfigWindow
    :members:

stat_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.stat_window.StatWindow
    :members:

login_history_window.py
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.login_history_window.LoginHistoryWindow
    :members:

server_console_interface.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.server_console_interface.run_server_console_interface
    :members:


