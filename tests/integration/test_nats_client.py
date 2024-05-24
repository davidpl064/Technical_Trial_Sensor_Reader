import asyncio

import pytest

from sensor_reader.app import AppSensorReader
from sensor_reader.data.custom_types import NatsUrl


class TestNatsClient:
    @pytest.mark.parametrize(
        "uri_message_server, expected_log_message, expected_connected",
        [
            (
                "nats://localhost:4222",
                "Successfully connected to NATS server on URI: nats://localhost:4222",
                True,
            )
        ],
    )
    @pytest.mark.asyncio
    async def test_connect_to_server(
        self, uri_message_server, expected_log_message, expected_connected, caplog
    ):
        freq_read_data = 5
        uri_db_server = "127.0.0.1:5432"

        app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)

        # Modify URI for NATS server
        app_sensor_reader.uri_message_server = NatsUrl(url=uri_message_server)

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_message_server()

        assert expected_connected == flag_connected

        # Get the captured log records
        log_records = caplog.records

        # Assert that the log message is captured
        assert any(expected_log_message in record.message for record in log_records)

        # Close connection
        await app_sensor_reader.disconnect_from_message_server()
        await asyncio.sleep(5)
