import requests
from config import (
    KEY,
    TOKEN
)

HEADERS = {
    "Accept": "application/json"
}

PARAMS = {
    'key': KEY,
    'token': TOKEN
}


def get_count_cards_in_column(id):
    url = f"https://api.trello.com/1/lists/{id}/cards"
    response = requests.request(
        "GET",
        url,
        headers=HEADERS,
        params=PARAMS
    )
    return response


def get(url: str) -> 'requests.models.Response':
    response = requests.request(
        "GET", url,
        headers=HEADERS, params=PARAMS
    )
    return response


def put(url: str, body: tuple) -> 'requests.models.Response':
    response = requests.request(
        "PUT", url, headers=HEADERS,
        data=body, params=PARAMS
    )
    return response
