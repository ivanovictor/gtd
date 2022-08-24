"""Load config from environment variables"""
from os import environ, path
from dotenv import load_dotenv

"""Load variables from .env"""
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, 'config.env'))

"""Database config"""
DATABASE_HOST = environ.get('DATABASE_HOST')
DATABASE_USER = environ.get('DATABASE_USER')
DATABASE_PASSWORD = environ.get('DATABASE_PASSWORD')
DATABASE_PORT = environ.get('DATABASE_PORT')
DATABASE_NAME = environ.get('DATABASE_NAME')

"""Board name"""
BOARD_ID = environ.get('BOARD_ID')

"""Authorization"""
LOGIN = environ.get('LOGIN')
PASS = environ.getn('PASS')

"""List of column id's"""
BACKLOG_ID = environ.get('BACKLOG_ID')
CURRENT_TASKS_ID = environ.get('CURRENT_TASKS_ID')
TASKS_FOR_LATER_ID = environ.get('TASKS_FOR_LATER_ID')
DONE_ID = environ.get('DONE_ID')

"""Key and Token for connect API Trello"""
KEY = environ.get('KEY')
TOKEN = environ.get('TOKEN')
