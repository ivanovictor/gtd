import requests
import json
import psycopg2
import time
from datetime import datetime
import pytz
from config import (
    KEY,
    TOKEN,
)

def sortTrash(db):

    id = "5fa291a201e844109fca505f"
    url = f"https://api.trello.com/1/lists/{id}/cards"
    params = {"key": KEY, "token": TOKEN}

    queryGetDate = '''
        select date 
        from trello.createcard
        where cardid = %s
    '''

    headers = {
       "Accept": "application/json"
    }

    response = requests.request(
       "GET",
       url,
       headers=headers,
       params=params
    )

    tz = pytz.timezone('Europe/Moscow')

    ListCard = []

    try:
       for x in json.loads(response.text):
           createDate = db.select_rows(queryGetDate, (x["id"],))
           ListCard.append([x["id"], x["pos"], createDate])
    except:
       print("error")

    N = len(ListCard)

    firstPosition = ListCard[0][1]
    lastPosition = ListCard[N-1][1]

    # Внешний цикл, количество проходов N-1. Сортировка по дате
    for i in range(N - 1):
        # Внутренний цикл, N-i-1 проходов
        for j in range(0, N - i - 1):
            # Меняем элементы местами
            if ListCard[j][2] < ListCard[j + 1][2]:
                temp = ListCard[j]
                ListCard[j] = ListCard[j + 1]
                ListCard[j + 1] = temp

    if ListCard[0][1] != firstPosition and (datetime.now(tz) - ListCard[0][2][0][0]).total_seconds() > 5 * 60:
        time.sleep(1)
        ListCard[0][1] = firstPosition/2
        url = f"https://api.trello.com/1/cards/{ListCard[0][0]}"
        body = {'pos': ListCard[0][1]}
        response = requests.request(
            "PUT",
            url,
            headers=headers,
            data=body,
            params=params
        )

    if ListCard[N-1][1] != lastPosition and (datetime.now(tz) - ListCard[0][2][0][0]).total_seconds() > 5 * 60:
        time.sleep(1)
        ListCard[N-1][1] = lastPosition + 2**16
        url = f"https://api.trello.com/1/cards/{ListCard[N-1][0]}"
        body = {'pos': ListCard[N-1][1]}
        response = requests.request(
            "PUT",
            url,
            headers=headers,
            data=body,
            params=params
        )

    ListCardPos = []
    for x in ListCard:
        ListCardPos.append(x[1])

    # Внешний цикл, количество проходов N-1. Сортировка по pos
    for i in range(N - 1):
        # Внутренний цикл, N-i-1 проходов
        for j in range(0, N - i - 1):
            # Меняем элементы местами
            if ListCardPos[j] > ListCardPos[j + 1]:
                temp = ListCardPos[j]
                ListCardPos[j] = ListCardPos[j + 1]
                ListCardPos[j + 1] = temp

    for i in range(N-2):
        if (ListCard[i+1][1] > ListCard[i+2][1] or (ListCard[i+1][1] < ListCard[i+2][1] and ListCard[i+1][1] < ListCard[i][1])) and (datetime.now(tz) - ListCard[i+1][2][0][0]).total_seconds() > 5 * 60:
            time.sleep(1)
            firstNumber = ListCard[i][1]
            secondNumber = ListCardPos[i+1]
            k = (firstNumber + secondNumber)/2
            ListCard[i+1][1] = k
            url = f"https://api.trello.com/1/cards/{ListCard[i+1][0]}"
            body = {'pos': ListCard[i+1][1]}
            response = requests.request(
                "PUT",
                url,
                headers=headers,
                data=body,
                params=params
            )