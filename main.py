from datetime import datetime
import time
from Activity import insert_activity
from archiveDone import execution_archiving
from sortTrash import sortTrash
from quantity_change import quantity_change
from config import (
    DATABASE_HOST,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_NAME
)
from db import Database

db = Database(
    DATABASE_HOST,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_NAME
)

while True:
    try:
        insert_activity(db)
        execution_archiving(db)
        sortTrash(db)
        quantity_change(db)
        time.sleep(60*2)
    except Exception as e:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f"Ошибка в цикле главной программы main.py: {e}",
              current_time)
        time.sleep(60)



