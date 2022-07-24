import requests
import json
from datetime import datetime
import pytz
from db import Database
from library import get, put
from log import logger
from config import (
    KEY,
    TOKEN,
    DONE_ID
)

# Quantity of cards in column "Done!" limited this number
CARDS_QUANTITY = 7

date_last_activity_query = """
select max(datelastactivity)
  from trello.archivedone
"""

insert_card_query = """
insert into trello.archivedone(id, dateLastActivity)
values(%s, %s)
"""

cards_count_query = """ 
select count(id)
  from trello.archivedone
"""

id_card_archived_query = """
select id
  from trello.archivedone
 order by datelastactivity asc
 limit 1
"""

delete_card_archived_query = """
delete from trello.archivedone
 where id = %s
"""

id_card_more_than_24_hours_query = """
select id
  from trello.archivedone a
 where EXTRACT(epoch FROM age(current_timestamp, datelastactivity))/3600 > 24
 order by datelastactivity asc
 limit 1
"""

local_tz = pytz.timezone('Europe/Moscow')
url_get_list_done = f"https://api.trello.com/1/lists/{DONE_ID}/cards"
url_delete_card = "https://api.trello.com/1/cards/"
body = {'closed': 'true'}


def convert_str_to_datetime(datetime_str):
    date_time = datetime.strptime(
        datetime_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    return date_time


def get_cards(request):
    cards = json.loads(request.text)
    cards.sort(key=lambda date: date["dateLastActivity"], reverse=True)
    return cards


def insert_card(db, cards):
    date_last_activity_db = db.select_rows(date_last_activity_query)[0][0]
    for card in cards:
        date_last_activity_trello = convert_str_to_datetime(
            card["dateLastActivity"])
        logger.debug(f"Date from API Trello: {date_last_activity_trello}, "
                     f"last card with date from db: {date_last_activity_db}, "
                     f"date equals: "
                     f"{date_last_activity_trello == date_last_activity_db}")
        if date_last_activity_trello != date_last_activity_db:
            list_value = [
                card["id"],
                date_last_activity_trello]
            try:
                db.insert_rows(insert_card_query, list_value)
                logger.info(f"Row with card id {card['id']} "
                            f"inserted successfully")
            except NameError:
                logger.error(f"Row inserted with error: {NameError}")
        else:
            break


def delete_card(db, body, CARDS_QUANTITY):
    cards_count = db.select_rows(cards_count_query)[0][0]
    while cards_count > CARDS_QUANTITY:
        id = db.select_rows(id_card_archived_query)[0][0]
        status_code = put(url_delete_card + f"{id}", body).status_code
        if status_code == 200:
            try:
                db.delete_rows(delete_card_archived_query, (id,))
                logger.info(f"Card with {id} archived successfully")
            except Exception as e:
                logger.error(f"Card with {id} not archived, error: {e}")
                break
        else:
            logger.error(f"Card with {id} not archived")
        cards_count -= 1

    if cards_count <= CARDS_QUANTITY and \
            db.select_rows(id_card_more_than_24_hours_query):
        id = db.select_rows(id_card_more_than_24_hours_query)[0][0]
        status_code = put(url_delete_card + f"{id}", body).status_code
        if status_code == 200:
            db.delete_rows(delete_card_archived_query, (id,))
            logger.info(f"Card with {id} archived successfully")
        else:
            logger.error(f"Card with {id} not archived")


def execution_archiving(db):
    request = get(url_get_list_done)
    status_code = request.status_code
    if status_code == 200:
        logger.info("GET request for column 'Done!' completed successfully")
        insert_card(db, get_cards(request))
        delete_card(db, body, CARDS_QUANTITY)
    else:
        logger.error(
            f"GET request from column 'Done!' completed with error, status: "
            f"{status_code}"
        )
