import asyncio
import sys
from collections.abc import Coroutine
from datetime import datetime

import fire
import nats
from loguru import logger
from nats.aio.msg import Msg
from nats.errors import ConnectionClosedError, NoServersError, TimeoutError

from sensor_reader.data.custom_types import AppCommandActions, NatsUrl
from sensor_reader.db.db_client import PostgresDbClient
from tests.mocks.sensor_infrared import SensorInfrared


class AppSensorReader:
    """
    Class to capture sensor data and pyblish it to several services including: NATS server,
    PostgreSQL.
    """

    def __init__(self, freq_report_data: int, uri_db_server: str):
        self.flag_on_standby = False
        self.flag_exit = False
        self.topic_raw_data = "sensors"
        self.topic_command = "app_command"
        self.topic_publishing = "publishing"
        self.sleep_on_standby = 0.2
        self.sensor_data_array_length = 64
        self.last_sensor_data: list[int] | None = None

        self.freq_report_data = freq_report_data
        self.uri_message_server = NatsUrl(url="nats://localhost:4222")

        self.db_client = PostgresDbClient(uri_db_server)
        # self.mock_sensor = SensorInfrared(min_range_value, max_range_value)

    async def connect_to_message_server(self):
        """
        Connect to set NATS server.

        Returns:
            bool: result of the connection. True if successfull connection, False otherwise.
        """
        flag_connected: bool = False
        while not flag_connected:
            # Connect to local NATS server
            try:
                self.nats_client = await nats.connect(
                    self.uri_message_server.url,
                    connect_timeout=10,
                    error_cb=self.connect_errors_handler,
                )
                flag_connected = True
            except Exception as err:
                logger.error(f"Cannot connect to NATS message server: {err}")
                await asyncio.sleep(2)

        logger.success(
            f"Successfully connected to NATS server on URI: {self.uri_message_server.url}"
        )

        # Subscribe to sensor data publishing topic
        self.sub_raw_data = await self.nats_client.subscribe(
            self.topic_raw_data, cb=self.handler_raw_data_messages
        )

        # Subscribe to app command topic
        self.sub_app_command = await self.nats_client.subscribe(
            self.topic_command, cb=self.handler_command_messages
        )

        return flag_connected

    async def connect_errors_handler(
        self, err: ConnectionClosedError | NoServersError | TimeoutError
    ):
        """Callback to handle connection errors to NATS server.

        Args:
            err (ConnectionClosedError, NoServersError, TimeoutError): encountered error in connection to NATS server.
        """
        logger.error(f"Cannot connect to NATS message server: {err}")

    async def connect_to_db(self):
        """Connect to set database.

        Returns:
            bool: result of the connection. True if successfull connection, False otherwise.
        """
        flag_connected = False
        while not flag_connected:
            logger.info(
                f"Trying to connect to database server on URI: {self.db_client.address_db_server.uri}"
            )
            db_conn, error_code = self.db_client.connect()

            if error_code is None:
                flag_connected = True
            else:
                await asyncio.sleep(2)

        logger.success(
            f"Successfully connected to database server on URI: {self.db_client.address_db_server.uri}"
        )

        # Setup basic data structure
        self.db_client.setup_data_structure()

        return flag_connected

    async def handler_raw_data_messages(self, msg: Msg):
        """Callback to handle messages containing raw data from sensors.

        Args:
            msg (Msg): message containing raw data from infrared sensor.
        """
        subject = msg.subject
        reply = msg.reply
        raw_data: str = msg.data.decode()
        logger.debug(f"Received raw sensor data on '{subject}' topic: {raw_data}")

        # Respond to the message if needed
        if reply:
            await self.nats_client.publish(reply, b"OK")

        raw_data = raw_data[1:-1]
        raw_data = raw_data.replace("\n", ",")
        raw_data = raw_data.replace("  ", ",")

        index = 0
        data_parsed: list[int] | None = []
        while index <= len(raw_data) - 1:
            character = raw_data[index]
            if character in [" ", "[", "]", ",", "\n"]:
                index += 1
                continue

            try:
                character_numeric = True
                index_last_digit = index
                while character_numeric:
                    if index_last_digit + 1 > len(raw_data) - 1:
                        break
                    if raw_data[index_last_digit + 1].isnumeric() is True:
                        index_last_digit += 1
                    else:
                        character_numeric = False
                        break

                data_parsed.append(int(raw_data[index : index_last_digit + 1]))  # type: ignore
                index = index_last_digit + 1
            except Exception as err:
                logger.error(
                    f"Raw data could not be parsed, removing last captured data: {raw_data}."
                    f"Error: {err}"
                )
                data_parsed = None

        self.last_sensor_data = data_parsed

    async def handler_command_messages(self, msg: Msg):
        """Callback to handle command messages that control app state.

        Args:
            msg (Msg): command message setting state of the app. Three execution modes
                ares currently supported:
                    1. AppCommandActions.START: start capturing and publushind data from sensors.
                    2. AppCommandActions.STOP: stop capturing and publushind data from sensors.
                    Sets the app on standby state.
                    3. AppCommandActions.EXIT: stop all functionalities and exits app main loop.
        """
        subject = msg.subject
        data = msg.data.decode()
        logger.debug(f"Received a message on '{subject}' topic: {data}")

        # Parse command data
        data = AppCommandActions(int(data))
        match data:
            case AppCommandActions.START:
                self.flag_on_standby = False
                logger.info("Restarting sensor data capturing and processing.")

            case AppCommandActions.STOP:
                self.flag_on_standby = True
                logger.info("Stopping sensor data capturing and processing.")

            case AppCommandActions.EXIT:
                logger.info("Closing app ...")
                await self.close()

    async def run(self):
        """Run main loop of the app."""
        await self.connect_to_message_server()
        await self.connect_to_db()

        while not self.flag_exit:
            await self.process_sensor_data()

        logger.info("All closed, exiting")

    async def process_sensor_data(self):
        """Process raw data from input sensors and store it in a database."""
        if self.flag_on_standby:
            logger.info("Sensor reader app on standby.")
            await asyncio.sleep(self.sleep_on_standby)
            return

        # Get sensor data and its associated timestamp
        new_sensor_data = self.read_data_from_sensor()
        timestamp = datetime.now()

        if not new_sensor_data:
            await asyncio.sleep(self.sleep_on_standby)
            return

        await self.publish_sensor_data(new_sensor_data)

        # Save new read sensor data on database
        self.db_client.save_data(new_sensor_data, timestamp)

        # Asynchronously wait for next data update
        await asyncio.sleep(self.freq_report_data)

    def read_data_from_sensor(self):
        """Read raw data from sensors.

        Returns:
            list[int] | None: raw data from sensor. None in case of corrupted data.
        """
        if not self.last_sensor_data:
            return self.last_sensor_data

        # Check data has been correctly parsed
        if len(self.last_sensor_data) != self.sensor_data_array_length:
            logger.warning("Bad data read from sensor. Data will be discarded.")
            self.last_sensor_data = None

        # last_sensor_data = self.mock_sensor.get_data()
        last_sensor_data = self.last_sensor_data
        logger.info(f"Read data: {last_sensor_data}")

        return last_sensor_data

    async def publish_sensor_data(self, last_sensor_data: list[int] | None):
        """Publish captured sensor data to a NATS topic.

        Args:
            last_sensor_data (list[int] | None): raw data from sensor. None in case of corrupted data.
        """
        await self.nats_client.publish(
            self.topic_publishing, str(last_sensor_data).encode()
        )

    async def disconnect_from_message_server(self):
        """Disconnect from NATS server and unsubscribe from capturing and command topics."""
        # Remove interest in subscription.
        await self.sub_raw_data.unsubscribe()
        await self.sub_app_command.unsubscribe()

        # Close connection to NATS server after processing remaining messages
        await self.nats_client.drain()

    async def close(self):
        """Close all connections to external services and update app status to exit."""
        # Update app state to exiting
        self.flag_exit = True
        self.flag_on_standby = True

        # Close connection to NATS server
        await self.disconnect_from_message_server()

        # Close database connection
        self.db_client.disconnect()


async def run_concurrent_tasks(tasks: list[Coroutine]):
    """Run input tasks concurrently.

    Args:
        tasks (list[Coroutine]): list of tasks to be run concurrently.
    """
    await asyncio.gather(*tasks)


def main(
    sensor_type: str,
    freq_read_data: int,
    uri_db_server: str,
    min_range_value: int | None = None,
    max_range_value: int | None = None,
    log_level: str = "INFO",
):
    """Main method to run main lopp of AppSensorReader and input "mock infrared sensor" (if set).

    Args:
        sensor_type (str): type of input infrared sensor. Can be mock or real.
        freq_read_data (int): frequency at which raw sensor data is read.
        uri_db_server (str): URI to database server.
        min_range_value (int | None, optional): min. value returned by input sensor. Defaults to None.
        max_range_value (int | None, optional): max. value returned by input sensor. Defaults to None.
        log_level (str, optional): level of logging messages. Defaults to "INFO".
    """
    # Configure logging level
    logger.configure(handlers=[{"sink": sys.stderr, "level": log_level}])

    tasks = []
    if sensor_type == "mock":
        uri_message_server = "nats://localhost:4222"
        mock_sensor = SensorInfrared(
            min_range_value, max_range_value, uri_message_server  # type: ignore
        )
        tasks.append(mock_sensor.run())

    app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)
    tasks.append(app_sensor_reader.run())
    # asyncio.run(app_sensor_reader.run())

    asyncio.run(run_concurrent_tasks(tasks))


if __name__ == "__main__":
    fire.Fire(main)
