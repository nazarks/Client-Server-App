"""
Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""
import ipaddress
import platform
import socket
import subprocess

PING_COUNT = 1


def get_ping_param():
    # Дополнительные параметры для команды ping в зависимости от операционной системы
    if platform.system() in ("Linux", "Linux2", "darwin"):
        return "-c"
    return "-n"


def get_ip_by_host_name(host_name):
    # Получим ip address по имени хоста
    try:
        return socket.gethostbyname(host_name)
    except:
        pass


def host_ping(host_address_list):
    """
    :param host_address_list: list ip addresses host list
    :return: dict {'host': status}
    """
    answer = {}
    ping_param = get_ping_param()
    for host in host_address_list:
        resolved_ip = get_ip_by_host_name(host)
        try:
            if resolved_ip:
                host = ipaddress.ip_address(resolved_ip)
            else:
                host = ipaddress.ip_address(host)
        except ValueError:
            pass
        args = ["ping", str(host), ping_param, str(PING_COUNT)]
        ping_sub_proc = subprocess.run(args, stdout=subprocess.PIPE)
        if ping_sub_proc.returncode == 0:
            answer[host] = "Reachable"
            print(f"{host} - Узел доступен")
        else:
            answer[host] = "Unreachable"
            print(f"{host} - Узел не доступен")
    return answer


if __name__ == "__main__":
    address_list = (
        "www.ya.ru",
        "www.google.ru",
        "github.com",
        "127.0.0.1",
        "216.58.210.163",
        "130.0.0.11111",
    )

    host_ping(address_list)
