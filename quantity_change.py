"""
1. Создаем таблицу с 4 колонками:
    1. id - id записи в таблице
    2. list_id - уникальный номер списка в Trello
    3. date_time - время, в которое было добавлено количество
    4. quantity - количесво карточек в колонке

2. Каждый час записывать в базу данных количество
3. Если время больше 01:00 и записей нет, то сделать запись прямо сейчас. В остальных случаях по расписанию
4. Для отображения на графике выбирать наибольшее количество за день
5. Можно в main цикле каждый N раз выпполнять функцию
"""
import datetime
import pytz
import json
from library import get_count_cards_in_column
from db import Database
from config import (
    BACKLOG_ID,
    CURRENT_TASKS_ID,
    TASKS_FOR_LATER_ID
)


list_columns = [
    BACKLOG_ID,
    CURRENT_TASKS_ID,
    TASKS_FOR_LATER_ID
]

timezone = pytz.timezone('Europe/Moscow')

insert_quantity_query = """
    insert into trello.quantity_change(list_id, date_time, quantity)
    values(%s, %s, %s)
"""

last_entry_query = """
    select max(date_time)
      from trello.quantity_change
"""


def insert_count_today(db, list_columns):
    for column in list_columns:
        columns = [
            column,
            datetime.datetime.now(timezone),
            len(json.loads(get_count_cards_in_column(column).text))
        ]
        db.insert_rows(insert_quantity_query, columns)


def quantity_change(db):
    datetime_last_entry = db.select_rows(last_entry_query)
    datetime_difference = (datetime.datetime.now(timezone) -
                           datetime_last_entry[0][0]).total_seconds()
    if datetime_difference >= 60 * 60:
        insert_count_today(db, list_columns)

