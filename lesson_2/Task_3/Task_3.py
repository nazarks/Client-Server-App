"""
3. Задание на закрепление знаний по модулю yaml.
 Написать скрипт, автоматизирующий сохранение данных
 в файле YAML-формата.
Для этого:

Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим в кодировке
ASCII(например, €);

Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла с помощью
параметра default_flow_style, а также установить возможность работы
с юникодом: allow_unicode = True;

Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""
import yaml

DATA = {
    "frameworks": ["Django", "FastApi", "Flask"],
    "count": 3,
    "release_date": {"Django": "21 июля 2005 года", "Flask": "1 апреля 2010 года", "FastApi": "5 Декабря 2018 года"},
}

with open("data_file.yaml", "w", encoding="utf-8") as f:
    yaml.dump(data=DATA, stream=f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=4)

with open("data_file.yaml", "r", encoding="utf-8") as f:
    data_read_from_yaml = yaml.load(stream=f, Loader=yaml.SafeLoader)

assert DATA == data_read_from_yaml, "Данные не совпадают"
print("Данные совпадают")
