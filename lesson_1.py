# Task 1
# Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и
# проверить тип и содержание соответствующих переменных. Затем с помощью
# онлайн-конвертера преобразовать строковые представление в формат Unicode и также
# проверить тип и содержимое переменных.

str_1 = "разработка"
str_2 = "сокет"
str_3 = "декоратор"
print(type(str_1), str_1)
print(type(str_2), str_2)
print(type(str_3), str_3)

# 'разработка' в формате unicode
str_1 = "\u0440\u0430\u0437\u0440\u0430\u0431\u043E\u0442\u043A\u0430"

# 'сокет' в формате unicode
str_2 = "\u0441\u043E\u043A\u0435\u0442"

# 'декоратор' в формате unicode
str_3 = "\u0434\u0435\u043A\u043E\u0440\u0430\u0442\u043E\u0440"

print(type(str_1), str_1)
print(type(str_1), str_2)
print(type(str_1), str_3)

# Task 2
# Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в
# последовательность кодов (не используя методы encode и decode) и определить тип,
# содержимое и длину соответствующих переменных.

str_1 = b"class"
str_2 = b"function"
str_3 = b"method"

print(f"Тип {type(str_1)}, содержимое {str_1}, длина {len(str_1)}")
print(f"Тип {type(str_2)}, содержимое {str_2}, длина {len(str_2)}")
print(f"Тип {type(str_3)}, содержимое {str_3}, длина {len(str_3)}")

# Task 3
# Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
# байтовом типе.

print("\nВ байтовом виде невозможно записать слова: «класс», «функция»")

# Task 4
# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из
# строкового представления в байтовое и выполнить обратное преобразование (используя методы encode и decode).

bytes_1 = "разработка".encode(encoding="utf-8")
bytes_2 = "администрирование".encode(encoding="utf-8")
bytes_3 = "protocol".encode(encoding="utf-8")
bytes_4 = "standard".encode(encoding="utf-8")

print("\n", bytes_1, bytes_2, bytes_3, bytes_4)
print(
    bytes_1.decode(encoding="utf-8"),
    bytes_2.decode(encoding="utf-8"),
    bytes_3.decode(encoding="utf-8"),
    bytes_4.decode(encoding="utf-8"),
)
# Task 5
# Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
# байтовового в строковый тип на кириллице.

import subprocess

args = ["ping", "google.com", "-c 2"]
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
for line in subproc_ping.stdout:
    print(line.decode(encoding="cp866"))

# Task 6
# Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое
# программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
# Принудительно открыть файл в формате Unicode и вывести его содержимое

with open("test_file.txt", "w") as f:
    f.write(f"сетевое программирование\nсокет\nдекоратор\n")

with open("test_file.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line)
