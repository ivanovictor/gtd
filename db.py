import psycopg2
from loguru import logger


class Database:
    """PostgreSQL Database class"""

    def __init__(
            self,
            DATABASE_HOST,
            DATABASE_USER,
            DATABASE_PASSWORD,
            DATABASE_PORT,
            DATABASE_NAME
    ):
        self.host = DATABASE_HOST
        self.user = DATABASE_USER
        self.password = DATABASE_PASSWORD
        self.port = DATABASE_PORT
        self.dbname = DATABASE_NAME
        self.conn = None

    def connect(self):
        """Connect to a Postgres database"""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    dbname=self.dbname
                )
                logger.info("Connection opened successfully")
            except psycopg2.DatabaseError as e:
                logger.error(e)
                raise e

    def select_rows(self, query, values=''):
        """Run a SQL query to select rows from table"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(f"{query}", values)
            records = cur.fetchall()
            cur.close()
        return records

    def insert_rows(self, query, values):
        """Run a SQL query to insert rows into table"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(f"{query}", values)
            self.conn.commit()
            cur.close()

    def delete_rows(self, query, values):
        """Run a SQL query to delete rows from table"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(f"{query}", values)
            self.conn.commit()
            cur.close()

    def rollback(self):
        self.connect()
        self.conn.rollback()
