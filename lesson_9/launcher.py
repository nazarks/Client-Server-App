# script for running server and n clients, windows usage

import subprocess
import sys
import time

CLIENTS_NAME = ["Kate", "Ivan", "Nik", "John", "Admin"]


process = []
args = ["python", "server.py"]
process.append(subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE))
time.sleep(1)

while True:
    action = input("Выберите действие: q - выход, " "s - запустить клиенты: ")

    if action == "q":
        while process:
            p = process.pop()
            p.kill()
        print("Bye! Bye!")
        sys.exit(0)

    elif action == "s":
        clients_number = int(input(f"Сколько клиентов запустить? Максимальное количество {len(CLIENTS_NAME)}: "))
        if clients_number > len(CLIENTS_NAME):
            clients_number = len(CLIENTS_NAME)
        for i in range(clients_number):
            args = ["python", "client.py", "10000", "127.0.0.1", CLIENTS_NAME[i]]
            process.append(subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE))
