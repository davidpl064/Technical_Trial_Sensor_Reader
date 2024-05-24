import psycopg2
from loguru import logger
from psycopg2.extensions import connection, cursor

from sensor_reader.data.custom_types import IPAddressWithPort


class PostgresDbClient:
    """Class to define database client interface based on PostgreSQL."""

    def __init__(self, uri_db_server: str):
        self.db_name = "postgres"
        self.username = "sensor_reader"
        self.password = "1234"  # Password should not be hardcoded here
        self.address_db_server = IPAddressWithPort(uri=uri_db_server)

        self.timeout_connect = 10  # [s]
        self.db_conn: connection | None = None
        self.table_name = "sensor_data"

    def connect(self):
        """Connect to set PostgreSQL server.

        Returns:
            connection: connection to database server.
            [psycopg2.Error | None]: error code of the connection process.
        """
        try:
            self.db_conn: connection = psycopg2.connect(
                database=self.db_name,
                user=self.username,
                password=self.password,
                host=self.address_db_server.ip,
                port=self.address_db_server.port,
                connect_timeout=self.timeout_connect,
            )

        except psycopg2.Error as err:
            logger.error(f"Cannot connect to database: {err}")
            return self.db_conn, err

        return self.db_conn, None

    def setup_data_structure(self):
        """Set table data structure in case there was no previous existing data."""
        # Check previous existing data
        self.cursor = self.db_conn.cursor()
        flag_previous_data = self.check_existing_data(self.cursor)

        if flag_previous_data:
            return

        # Define basic structure of the database table
        self.cursor.execute(
            f"""CREATE TABLE {self.table_name}
            (id serial  PRIMARY KEY,
            value       INT[]    NOT NULL,
            timestamp   TIMESTAMPTZ NOT NULL);"""  # noqa E231 E241
        )
        self.db_conn.commit()

    def check_existing_data(self, cursor: cursor):
        """Check already existing table data in database.

        Returns:
            bool: flag indicating previous existing data table. True if positive, False otherwise.
        """
        try:
            query = """
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """
            cursor.execute(query)
            tables = cursor.fetchall()

            for table in tables:
                if self.table_name in table[0]:
                    return True

        except psycopg2.Error as err:
            logger.error(f"Error querying tables: {err}")

        return False

    def save_data(self, data: list[int], timestamp: int):
        """Save data to database.

        Args:
            data (list[int]): data to be stored.
            timestamp (int): timestamp of the data.
        """
        self.cursor.execute(
            f"INSERT INTO {self.table_name} (value, timestamp) VALUES (%s, %s)",
            (data, timestamp),
        )
        self.db_conn.commit()  # type: ignore

    def disconnect(self):
        """Close cursor and connection to server database."""
        self.cursor.close()
        self.db_conn.close()
