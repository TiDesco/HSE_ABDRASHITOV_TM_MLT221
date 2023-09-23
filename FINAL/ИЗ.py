from datetime import date
import requests
from bs4 import BeautifulSoup
import json
import os
from decimal import Decimal
import openpyxl


class ParserCBRF:

    @staticmethod
    def __currency(cur):
        url = 'https://www.cbr.ru/currency_base/dynamics/'
        r = requests.get(url)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        cur_dict = {i.text.strip(): i['value'] for i in soup.find("select").find_all("option")}

        if cur in cur_dict.keys():
            return cur_dict[cur]
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'

   
    def __get_page(self, cur):
        url_currency = self.__currency(cur)
        today = date.today().strftime("%d.%m.%Y")
        url_cur = f'https://www.cbr.ru/currency_base/dynamics/' \
                  f'?UniDbQuery.Posted=True&UniDbQuery.so=1&UniDbQuery.mode=1&UniDbQuery.' \
                  f'date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ={url_currency}&UniDbQuery.' \
                  f'From=01.07.1992&UniDbQuery.To={today}'
        r_cur = requests.get(url_cur)
        return r_cur.text

   
    def __cb_parser(self, cur):
        html = self.__get_page(cur)
        soup = BeautifulSoup(html, "html.parser")
        table = [i.text for i in soup.find("table", {"class": "data"}).find_all("td")][1:]
        return table

    
    def __cb_dict(self, cur):
        cb_date_rate = self.__cb_parser(cur)
        cb_date = cb_date_rate[0::3]
        cb_measure = cb_date_rate[1::3]
        cb_rate = cb_date_rate[2::3]
        if cb_date == cb_measure == cb_rate:
            table_dict = {cb_date[i]: (cb_rate[i], cb_measure[i]) for i in range(len(cb_date))}
        else:
            table_dict = {cb_date[i]: (cb_rate[i], cb_measure[i])
                          for i in range(min(len(cb_date), len(cb_measure), len(cb_rate)))}
        return table_dict

    
    def cb_excel(self, cur):
        if self.__currency(cur) != 'Возможно Вы ошиблись в написании наименования валюты.':
            cb_date_rate = self.__cb_parser(cur)
            name_currency = cur
            cb_date = cb_date_rate[0::3]
            cb_measure = cb_date_rate[1::3]
            cb_rate = cb_date_rate[2::3]

            book = openpyxl.Workbook()
            sheet = book.active
            sheet['A1'] = 'Дата'
            sheet['B1'] = 'Курс'
            sheet['C1'] = 'За кол-во'

            if cb_date == cb_measure == cb_rate:
                for i in range(len(cb_date)):
                    sheet[f'A{i + 2}'] = cb_date[i]
                    sheet[f'B{i + 2}'] = cb_rate[i]
                    sheet[f'C{i + 2}'] = cb_measure[i]
                book.save(f'{name_currency}.xlsx')
                book.close()
            else:
                for i in range(min(len(cb_date), len(cb_measure), len(cb_rate))):
                    sheet[f'A{i + 2}'] = cb_date[i]
                    sheet[f'B{i + 2}'] = cb_rate[i]
                    sheet[f'C{i + 2}'] = cb_measure[i]
                book.save(f'{name_currency}.xlsx')
                book.close()

            if not os.path.exists('parsed_data'):
                os.mkdir('parsed_data')

            if os.path.exists(f'./parsed_data/{name_currency}.xlsx'):
                os.remove(f'./parsed_data/{name_currency}.xlsx')
            os.rename(f'./{name_currency}.xlsx', f'./parsed_data/{name_currency}.xlsx')
            return 'Создание Excel-таблицы прошло успешно.'
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'

   
    def cb_json(self, cur):
        if self.__currency(cur) != 'Возможно Вы ошиблись в написании наименования валюты.':
            cb_date_rate = self.__cb_dict(cur)
            name_currency = cur
            if not os.path.exists('parsed_data'):
                os.mkdir('parsed_data')
            with open(f"{name_currency}.json", "w") as json_file:
                json.dump(cb_date_rate, json_file, indent=4)

            if os.path.exists(f'./parsed_data/{name_currency}.json'):
                os.remove(f'./parsed_data/{name_currency}.json')
            os.rename(f'./{name_currency}.json', f'./parsed_data/{name_currency}.json')
            return 'Сериализация данных в json-файл прошла успешно.'
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'

  
    @staticmethod
    def cb_djson(cur):
        name_currency = cur
        if os.path.exists(f"./parsed_data/{name_currency}.json"):
            with open(os.path.join(f"./parsed_data/{name_currency}.json"), "r") as json_file:
                s = json.load(json_file)
            return s
        else:
            return f'Перепроверьте название json-файла. ' \
                   f'Возможно файла с названием "{name_currency}.json" не существует.'

    # метод для запуска Парсера
    def start(self, cur):
        if self.__currency(cur) != 'Возможно Вы ошиблись в написании наименования валюты.':
            return self.__cb_dict(cur)
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'



class CurrencyCBRF:


    @staticmethod
    def inf_currency_date(currency, day):
        cur_dict = ParserCBRF().start(currency)
        if cur_dict != 'Возможно Вы ошиблись в написании наименования валюты.':
            if day in cur_dict.keys():
                i_cur_date = cur_dict[day]
                return f'{i_cur_date[0]} рублей за {i_cur_date[1]} штук(у)'
            else:
                return f'Информация о дате {day} отсутствует на сайте ЦБ РФ. ' \
                       f'Попробуйте указать дату ближайшего к ней рабочего дня.'
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'


    @staticmethod
    def comparison(currency, day_old, day_new):
        cur_dict = ParserCBRF().start(currency)
        if cur_dict != 'Возможно Вы ошиблись в написании наименования валюты.':
            if day_old in cur_dict.keys() and day_new in cur_dict.keys():
                do = Decimal(cur_dict[day_old][0].replace(",", "."))
                dn = Decimal(cur_dict[day_new][0].replace(",", "."))
                comparison_result = do - dn
                if comparison_result < 0:
                    return f'Курс упал на {str(comparison_result)[1:]} руб.'
                elif comparison_result > 0:
                    return f'Курс вырос на {comparison_result} руб.'
                else:
                    return f'Величина курса не изменилась'
            elif day_old not in cur_dict.keys() and day_new in cur_dict.keys():
                return f'Информация о дате {day_old} отсутствует на сайте ЦБ РФ. ' \
                       f'Попробуйте указать дату ближайшего к ней рабочего дня.'
            elif day_old in cur_dict.keys() and day_new not in cur_dict.keys():
                return f'Информация о дате {day_new} отсутствует на сайте ЦБ РФ. ' \
                       f'Попробуйте указать дату ближайшего к ней рабочего дня.'
            elif day_old not in cur_dict.keys() and day_new not in cur_dict.keys():
                return f'Информация об указанных датах отсутствует на сайте ЦБ РФ. ' \
                       f'Попробуйте указать даты ближайшим к ним рабочих дней.'
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'


  
    @staticmethod
    def range_dates(currency, day_start, day_finish):
        cur_dict = ParserCBRF().start(currency)
        if cur_dict != 'Возможно Вы ошиблись в написании наименования валюты.':
            daf = list(cur_dict.keys()).index(day_start) + 1
            das = list(cur_dict.keys()).index(day_finish)
            exp = cur_dict.values()
            dad = {k: cur_dict[k] for k in list(cur_dict.keys())[das:daf]}
            return dad
        else:
            return 'Возможно Вы ошиблись в написании наименования валюты.'




if __name__ == '__main__':
    print(ParserCBRF().start('Доллар США'))
    print(ParserCBRF().cb_json('Евро'))
    print(ParserCBRF().cb_djson('Евро'))
    print(ParserCBRF().cb_excel('Китайский юань'))

    print(CurrencyCBRF().inf_currency_date('Белорусский рубль', '01.06.2023'))
    print(CurrencyCBRF().comparison('Английский фунт', '04.05.2023', '16.06.2023'))
    print(CurrencyCBRF().range_dates('Турецкая лира', '04.05.2023', '17.05.2023'))
