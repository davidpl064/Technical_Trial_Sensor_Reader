import asyncio

import nats
import numpy as np
from loguru import logger
from nats.errors import ConnectionClosedError, NoServersError, TimeoutError

from sensor_reader.data.custom_types import NatsUrl


class SensorInfrared:
    def __init__(
        self, min_range_value: int, max_range_value: int, uri_message_server: str
    ):
        data_resolution = 2**16
        assert (
            type(min_range_value) is int
        ), "'min_range_value' needed in case of mocked infrared sensor."
        assert (
            type(max_range_value) is int
        ), "'max_range_value' needed in case of mocked infrared sensor."

        assert (
            min_range_value >= 0 and min_range_value < data_resolution
        ), "'min_range_value' has to be positive and not exceed set sensor resolution 2^16."
        assert (
            max_range_value >= 0 and max_range_value < data_resolution
        ), "'max_range_value' has to be positive and not exceed set sensor resolution 2^16."

        self._min_value_range = min_range_value
        self._max_value_range = max_range_value
        self._last_data = np.random.randint(
            min_range_value, max_range_value + 1, size=64, dtype=np.uint16
        )
        self._uri_message_server = NatsUrl(url=uri_message_server)
        self._topic_raw_data = "sensors"
        self._freq_update_data = 1.0

    async def connect_to_message_server(self):
        """Connect to NATS server."""
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
                logger.debug(f"Cannot connect to NATS server: {err}")

    async def connect_errors_handler(
        self, err: ConnectionClosedError | NoServersError | TimeoutError
    ):
        logger.error(f"Mock sensor cannot connect to NATS message server: {err}")

    def generate_data_mock(self):
        # Mock sensor data readings as a random process
        # (probably not the real behaviour but enough for testing purposes)
        self._last_data = np.random.randint(
            self._min_value_range, self._max_value_range + 1, size=64, dtype=np.uint16
        )
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
