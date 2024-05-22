import asyncio
import sys

import nats
import numpy as np
from loguru import logger

from sensor_reader.data.custom_types import NatsUrl


class SensorInfrared:
    def __init__(
        self, min_value_range: int, max_value_range: int, uri_message_server: str
    ):
        self._min_value_range = min_value_range
        self._max_value_range = max_value_range
        self._last_data = np.random.randint(
            min_value_range, max_value_range + 1, size=1, dtype=np.uint16
        )[0]
        self._uri_message_server = NatsUrl(url=uri_message_server)
        self._topic_raw_data = "sensors"
        self._freq_update_data = 1.0

    async def connect_to_message_server(self):
        flag_connected = False
        while not flag_connected:
            # Connect to local NATS server
            try:
                self.nats_client = await nats.connect(
                    self._uri_message_server.url,
                    connect_timeout=10,
                    error_cb=self.connect_errors_handler,
                )
                flag_connected = True
            except Exception as err:
                await asyncio.sleep(2)

    async def connect_errors_handler(self, err):
        logger.error("Mock sensor cannot connect to NATS message server")

    def generate_data_mock(self):
        # Mock sensor data readings as a random process (probably not the real behaviour but enough for testing purposes)
        self._last_data = np.random.randint(
            self._min_value_range, self._max_value_range + 1, size=1, dtype=np.uint16
        )[0]
        logger.debug(f"New sensor data generated: {self._last_data}")

    def get_data(self):
        self.generate_data_mock()
        return self._last_data

    async def run(self):
        await self.connect_to_message_server()

        while True:
            # Emulate new data reading and publish them at set frequency
            self.generate_data_mock()
            await self.publish_data()

            await asyncio.sleep(self._freq_update_data)

    async def publish_data(self):
        await self.nats_client.publish(
            self._topic_raw_data, str(self._last_data).encode()
        )
