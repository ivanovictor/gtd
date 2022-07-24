import json
from datetime import datetime
from db import Database
import psycopg2
from psycopg2 import errors
from library import get
from log import logger
from config import (
    KEY,
    TOKEN,
    BOARD_ID
)


insert_createcard = """
    insert into trello.createcard(id, cardname, listname, listid, type, 
    date, cardid) values(%s, %s, %s, %s, %s, %s, %s)
"""

insert_card_link = """insert into trello.card_link(id_card, link) 
values (%s, %s)"""

insert_cardmove = """
    insert into trello.cardmove(id, cardid, cardname, listbeforeid, 
    listbeforename, listafterid, listaftername, type, date) 
    values(%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

insert_deletecard = """
    insert into trello.deletecard(id, cardid, listid, listname, type, date) 
    values(%s, %s, %s, %s, %s, %s)
"""


def get_activity(page):
    url_get_activity = f"https://api.trello.com/1/boards/{BOARD_ID}/actions?" \
                       f"filter=all&limit=50&page={page}&display=true" \
                       f"&key={KEY}&token={TOKEN}"
    activity = get(url_get_activity)
    return activity


def insert_activity(db):
    page = 0
    var_continue = True
    while get_activity(page).status_code == 200 and var_continue is True:
        for entry in json.loads(get_activity(page).text):
            if entry["type"] == 'createCard':
                id = entry["id"]
                cardname = entry["data"]["card"]["name"]
                listname = entry["data"]["list"]["name"]
                listid = entry["data"]["list"]["id"]
                typecard = entry["type"]
                carddate = entry["date"]
                cardid = entry["data"]["card"]["id"]
                link = entry["data"]["card"]["shortLink"]
                listcreatecard = [id, cardname, listname, listid,
                        typecard, carddate, cardid]
                list_for_link = [cardid, link]
                try:
                    db.insert_rows(insert_createcard, listcreatecard)
                    db.insert_rows(insert_card_link, list_for_link)
                    logger.info(f"rows with card id {id} and link"
                                f" inserted to createcard and card_link"
                                f" table successfully")
                except NameError:
                    logger.error(f"row inserted to createcard "
                                 f"with error: {NameError}")
                    db.rollback()
                    break
                except psycopg2.errors.lookup("23505"):
                    logger.error(f"card with id {id} already "
                                 f"added to createcard table")
                    db.rollback()
                    var_continue = False
                    break
            elif entry["type"] == 'updatecard' \
                    and 'listbefore' in entry["data"] \
                    and 'listafter' in entry["data"]:
                id = entry["id"]
                cardid = entry["data"]["card"]["id"]
                cardname = entry["data"]["card"]["name"]
                listBeforeId = entry["data"]["listBefore"]["id"]
                listBeforeName = entry["data"]["listBefore"]["name"]
                listAfterId = entry["data"]["listAfter"]["id"]
                listAfterName = entry["data"]["listAfter"]["name"]
                typecard = entry["type"]
                carddate = entry["date"]
                listcardmove = [id, cardid, cardname, listBeforeId,
                                listBeforeName, listAfterId, listAfterName,
                                typecard, carddate]
                try:
                    db.insert_rows(insert_cardmove, listcardmove)
                    logger.info(f"rows with card id {id}"
                                f" inserted to cardmove table successfully")
                except NameError:
                    logger.error(f"row inserted to cardmove "
                                 f"with error: {NameError}")
                    db.rollback()
                    break
                except psycopg2.errors.lookup("23505"):
                    logger.error(f"Card with id {id} already "
                                 f"added to cardmove table")
                    db.rollback()
                    var_continue = False
                    break
            elif entry["type"] == 'deletecard':
                id = x["id"]
                cardid = entry["data"]["card"]["id"]
                listid = entry["data"]["list"]["id"]
                listname = entry["data"]["list"]["name"]
                typecard = entry["type"]
                carddate = entry["date"]
                listdeletecard = [id, cardid, listid,
                                  listname, typecard, carddate]
                try:
                    db.insert_rows(insert_deletecard, listdeletecard)
                    logger.info(f"rows with card id {id}"
                            f" inserted to cardmove table successfully")
                except NameError:
                    logger.error(f"row inserted to deletecard "
                                 f"with error: {NameError}")
                    db.rollback()
                    break
                except psycopg2.errors.lookup("23505"):
                    logger.error(f"Card with id {id} already "
                                 f"added to deletecard table")
                    db.rollback()
                    var_continue = False
                    break
        if var_continue is False:
            logger.info(f"Новых активностей нет")
            break
        page += 1