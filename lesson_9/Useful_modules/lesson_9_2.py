"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
 Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""
import ipaddress

from lesson_9_1 import host_ping


def input_data(text):
    while True:
        input_address = input(text)
        try:
            ip_address_obj = ipaddress.ip_address(input_address)
            break
        except ValueError as e:
            print(f"Неправильный формат адреса: {e}")
    return ip_address_obj


def host_range_ping():
    ipaddress_start = input_data("Введите стартовый ip address: ")
    network = ipaddress.ip_network(f"{ipaddress_start}/24", strict=False)
    while True:
        ipaddress_end = input_data("Введите конечный ip address: ")

        # Проверяем, должен меняться только последний октет
        if ipaddress_end in network:
            break
        print(f"Адрес {ipaddress_end} из не этой подсети {network}")

    if ipaddress_start > ipaddress_end:
        ipaddress_start, ipaddress_end = ipaddress_end, ipaddress_start

    ipaddress_list = []
    while True:
        ipaddress_list.append(ipaddress_start)
        if ipaddress_start == ipaddress_end:
            break
        ipaddress_start += 1

    return host_ping(ipaddress_list)


if __name__ == "__main__":
    host_range_ping()
