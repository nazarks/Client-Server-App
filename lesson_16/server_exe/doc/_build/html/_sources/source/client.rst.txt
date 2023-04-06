client module
=============

Клиентское приложение для обмена сообщениями.
Поддерживает отправку сообщений пользователям которые находятся в сети

Поддерживает аргументы коммандной строки:

``python client.py -a address -p port``

client.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

client. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 2 элементов:

  * адрес сервера
  * порт

  Выполняет проверку на корректность номера порта.


client_database.py
~~~~~~~~~~~~~~~~~~

.. autoclass:: client.client_database.ClientDatabase
    :members:

transport.py
~~~~~~~~~~~~~~

.. autoclass:: client.transport.ClientTransport
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client.main_window.ClientMainWindow
    :members:

start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: client.start_dialog.UserNameDialog
    :members:


add_contact_dialog.py
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: client.add_contact_dialog.AddContactDialog
    :members:


del_contact.py
~~~~~~~~~~~~~~~

.. autoclass:: client.del_contact.DelContactDialog
    :members:
