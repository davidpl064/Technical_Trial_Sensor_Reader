from loguru import logger
import psycopg2
from datetime import datetime

from sensor_reader.data.custom_types import IPAddressWithPort

class PostgresDbClient():
    def __init__(self, uri_db_server: str):
        self.db_name = "postgres"
        self.username = "sensor_reader"
        self.password = "1234" # Password should not be hardcoded here
        self.address_db_server = IPAddressWithPort(uri=uri_db_server)

        self.timeout_connect = 10 # [s]
        self.db_conn = None
        self.table_name = "sensor_data"

    def connect(self):
        try:
            self.db_conn = psycopg2.connect(database = self.db_name, user = self.username, password = self.password, host = self.address_db_server.ip, port = self.address_db_server.port, connect_timeout=self.timeout_connect)

        except psycopg2.Error as err:
            logger.error(f"Cannot connect to database: {err}")

        return self.db_conn
    
    def setup_data_structure(self):
        # Check previous existing data
        self.cursor = self.db_conn.cursor()
        flag_previous_data = self.check_existing_data(self.cursor)

        if flag_previous_data:
            return

        # Define basic structure of the database table
        self.cursor.execute(f"""CREATE TABLE {self.table_name}
            (id serial  PRIMARY KEY,
            value       INT    NOT NULL,
            timestamp   TIMESTAMPTZ NOT NULL);
        """)
        self.db_conn.commit()

    def check_existing_data(self, cursor):
        try:
            query = ("""
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """)
            cursor.execute(query)
            tables = cursor.fetchall()

            for table in tables:
                if self.table_name in table[0]:
                    return True
            
        except psycopg2.Error as err:
            logger.error(f"Error querying tables: {err}")
        
        return False
    
    def save_data(self, data: int, timestamp: int):
        if data is None:
            data = 10
        self.cursor.execute(f"INSERT INTO {self.table_name} (value, timestamp) VALUES (%s, %s)", (int(data), timestamp))
        self.db_conn.commit()
