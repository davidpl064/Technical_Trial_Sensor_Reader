import argparse
import asyncio
from datetime import datetime
import fire
from loguru import logger
import numpy as np

import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

from tests.mocks.sensor_infrared import SensorInfrared
from sensor_reader.data.custom_types import (
    NatsUrl,
    AppCommandActions
)
from sensor_reader.db.db_client import PostgresDbClient

class AppSensorReader():
    def __init__(self, freq_report_data: int, uri_db_server: str, min_range_value: float, max_range_value: float):
        self.flag_on_standby = False
        self.flag_exit = False
        self.topic_raw_data = "sensors"
        self.topic_command = "app_command"
        self.topic_publishing = "publishing"
        self.sleep_on_standby = 0.2
        self.last_sensor_data = None

        self.freq_report_data = freq_report_data
        self.uri_message_server = NatsUrl(url="nats://localhost:4222")

        self.db_client = PostgresDbClient(uri_db_server)
        # self.mock_sensor = SensorInfrared(min_range_value, max_range_value)

    async def connect_to_message_server(self):
        flag_connected = False
        while not flag_connected:
            # Connect to local NATS server
            try:
                self.nats_client = await nats.connect(self.uri_message_server.url, connect_timeout=10, error_cb=self.connect_errors_handler)
                flag_connected = True
            except Exception as err:
                logger.error("Cannot connect to NATS message server")
                await asyncio.sleep(2)

        logger.info(f"Successfully connected to NATS server on URI: {self.uri_message_server.url}")

        # Subscribe to sensor data publishing topic
        self.sub_raw_data = await self.nats_client.subscribe(self.topic_raw_data, cb=self.handler_raw_data_messages)

        # Subscribe to app command topic
        self.sub_app_command = await self.nats_client.subscribe(self.topic_command, cb=self.handler_command_messages)

    async def connect_errors_handler(self, err):
        logger.error("Cannot connect to NATS message server")

    async def connect_to_db(self):
        flag_connected = False
        while not flag_connected:
            logger.info(f"Trying to connect to database server on URI: {self.db_client.address_db_server}")
            db_conn = self.db_client.connect()

            if db_conn is not None:
                flag_connected = True
            else:
                await asyncio.sleep(2)

        logger.info(f"Successfully connected to database server on URI: {self.db_client.address_db_server}")

        # Setup basic data structure
        self.db_client.setup_data_structure()

    async def handler_raw_data_messages(self, msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        print(f"Received raw sensor data on '{subject}': {data}")

        # Respond to the message if needed
        if reply:
            await self.nats_client.publish(reply, b'OK')

        self.last_sensor_data = data

    async def handler_command_messages(self, msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received a message on '{subject}': {data}")

        # Parse command data
        data = AppCommandActions(int(data))
        match data:
            case AppCommandActions.START:
                self.flag_on_standby = False
                logger.info("Starting sensor data capturing and processing.")

            case AppCommandActions.STOP:
                self.flag_on_standby = True
                logger.info("Stopping sensor data capturing and processing.")

            case AppCommandActions.EXIT:
                logger.info("Closing app ...") 
                await self.close()

    async def run(self):
        await self.connect_to_message_server()
        await self.connect_to_db()

        while not self.flag_exit:
            await self.process_sensor_data()

        logger.info("All closed, exiting")

    async def process_sensor_data(self):
        if self.flag_on_standby:
            await asyncio.sleep(self.sleep_on_standby)
            return
        
        # Get sensor data and its associated timestamp
        new_sensor_data = self.read_data_from_sensor()
        timestamp = datetime.now()

        await self.publish_sensor_data(new_sensor_data)

        # Save new read sensor data on database
        self.db_client.save_data(new_sensor_data, timestamp)

        # Asynchronously wait for next data update
        await asyncio.sleep(self.freq_report_data)

    def read_data_from_sensor(self):
        # last_sensor_data = self.mock_sensor.get_data()
        last_sensor_data = self.last_sensor_data
        logger.info(f"New read data: {last_sensor_data}")

        return last_sensor_data

    async def publish_sensor_data(self, last_sensor_data: np.uint16):
        await self.nats_client.publish(self.topic_publishing, str(last_sensor_data).encode())

    async def disconnect_from_server(self):
        # Remove interest in subscription.
        await self.sub_raw_data.unsubscribe()
        await self.sub_app_command.unsubscribe()

        # Close connection to NATS server after processing remaining messages
        await self.nats_client.drain()

    async def close(self):
        self.flag_exit = True
        self.flag_on_standby = True

        await self.disconnect_from_server()
        

async def run_concurrent_taks(tasks: list):
    await asyncio.gather(*tasks)

def main(sensor_type: str, freq_read_data: int, uri_db_server: str, min_range_value: int | None = None, max_range_value: int | None = None):
    tasks = []
    if sensor_type == "mock":
        assert type(min_range_value) is int, "'min_range_value' needed in case of mocked infrared sensor."
        assert type(max_range_value) is int, "'max_range_value' needed in case of mocked infrared sensor."

        uri_message_server = "nats://localhost:4222"
        mock_sensor = SensorInfrared(min_range_value, max_range_value, uri_message_server)
        tasks.append(mock_sensor.run())

    app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server, min_range_value, max_range_value)
    tasks.append(app_sensor_reader.run())
    # asyncio.run(app_sensor_reader.run())

    asyncio.run(run_concurrent_taks(tasks))


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument("sensor_type", type=str, help="Type of infrared sensor [mock, real].")
    # parser.add_argument("freq_read_data", type=int, help="Frequency of sensor reading [s].")
    # parser.add_argument("min_range_value", type=float, help="Minimum value for sensor data range.")
    # parser.add_argument("max_range_value", type=str, help="Maximum value for sensor data range.")
    # parser.add_argument(
    #     "--uri_nats_server",
    #     type=str,
    #     help="URI of NATS server",
    #     required=False,
    #     default="nats://localhost:4222",
    # )
    # args = parser.parse_args()
    fire.Fire(main)