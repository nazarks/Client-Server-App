"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt,
info_3.txt и формирующий новый «отчетный» файл в формате CSV.
"""
import csv
import os
import re

HEADERS = ("Изготовитель системы", "Название ОС", "Код продукта", "Тип системы")
FILE_NAME = "data_report.csv"


def get_file_list(ending):
    """
    get file list
    """
    file_list = []
    for root, dirs, files in os.walk("."):
        file_list = [filename for filename in files if filename.endswith(ending)]
        file_list.sort()
    return file_list


def get_result(str_for_search, data):
    result = re.findall(rf"{str_for_search}:\s+([^\n]+)", data)
    if result:
        return result[0].strip()


def get_data():
    """
    get data from .txt files
    """
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = [["Номер строки"]]
    file_list = get_file_list(".txt")
    if not file_list:
        raise Exception("File list is empty!")
    for file in file_list:
        with open(file, encoding="cp1251") as f:
            data = f.read()
            result = get_result("Изготовитель системы", data)
            os_prod_list.append(result)

            result = get_result("Название ОС", data)
            os_name_list.append(result)

            result = get_result("Код продукта", data)
            os_code_list.append(result)

            result = get_result("Тип системы", data)
            os_type_list.append(result)

    main_data[0].extend(HEADERS)
    j = 1
    for i in range(len(file_list)):
        row = [j, os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]]
        main_data.append(row)
        j += 1
    return main_data


def write_to_csv(file_name):
    data_to_write = get_data()
    with open(file_name, "w", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(data_to_write)
    print(f"Writtеn to file: {file_name}, {len(data_to_write) - 1} rows")


if __name__ == "__main__":
    write_to_csv(FILE_NAME)
