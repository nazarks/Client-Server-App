from time import sleep

from client.client_database import ClientDatabase
from client.transport import ClientTransport

user1 = "Nik"
database = ClientDatabase(user1)
transport = ClientTransport(port=7777, ip_address="127.0.0.1", database=database, username=user1)
transport.daemon = True
transport.start()
transport.sent_message_to_user("hi", to_user="Nik")
# msg = transport.create_user_message("hi", "Kate", account_name="Nik")
# transport.send_data("hi")
sleep(2)
transport.add_contact(username=user1, contact="Vasya")
# transport.sent_message_to_user("hi again", to_user="Nik", account_name="Nik")
sleep(2)
transport.add_contact(username=user1, contact="Vasya")
