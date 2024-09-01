import psycopg2
from fastapi import HTTPException

from app_config.settings import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


class DBManager:
    def __init__(self):
        self.db_host = DB_HOST
        self.db_name = DB_NAME
        self.db_user = DB_USER
        self.db_password = DB_PASSWORD

    async def connect_to_db(self):
        """
        Подключение к базе данных.
        """
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            return conn
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to database: {e}")