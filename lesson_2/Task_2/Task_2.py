"""
2. Задание на закрепление знаний по модулю json. Есть файл orders
в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий
его заполнение данными.

Для этого:
Создать функцию write_order_to_json(), в которую передается
5 параметров — товар (item), количество (quantity), цена (price),
покупатель (buyer), дата (date). Функция должна предусматривать запись
данных в виде словаря в файл orders.json. При записи данных указать
величину отступа в 4 пробельных символа;
Проверить работу программы через вызов функции write_order_to_json()
с передачей в нее значений каждого параметра.

ПРОШУ ВАС НЕ УДАЛЯТЬ ИСХОДНЫЙ JSON-ФАЙЛ
ПРИМЕР ТОГО, ЧТО ДОЛЖНО ПОЛУЧИТЬСЯ

{
    "orders": [
        {
            "item": "printer",
            "quantity": "10",
            "price": "6700",
            "buyer": "Ivanov I.I.",
            "date": "24.09.2017"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        }
    ]
}

вам нужно подгрузить JSON-объект
и достучаться до списка, который и нужно пополнять
а потом сохранять все в файл
"""

import json

FILE_NAME = "orders_new.json"


def write_to_json(file_name, item, quantity, price, buyer, date):
    """
    write data to json file
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File {FILE_NAME} not found! Start with empty order list.")
        data = {"orders": []}

    new_order = {
        "item": item,
        "quantity": quantity,
        "price": price,
        "buyer": buyer,
        "date": date,
    }
    data["orders"].append(new_order)

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(fp=f, indent=4, obj=data, ensure_ascii=False)


if __name__ == "__main__":
    write_to_json(FILE_NAME, "printer", "10", "6700", "Ivanov I.I.", "24.09.2017")
    write_to_json(FILE_NAME, "scaner", "20", "10000", "Petrov P.P.", "11.01.2018")
    write_to_json(FILE_NAME, "computer", "5", "40000", "Sidorov S.S.", "2.05.2019")
    write_to_json(FILE_NAME, "Компьютер", "50", "44000", "Ким", "02.05.2019")
