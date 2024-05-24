import asyncio
import pytest

from sensor_reader.app import AppSensorReader
from sensor_reader.data.custom_types import NatsUrl


class TestNatsClient:
    @pytest.mark.parametrize(
        "uri_db_server, expected_log_message, expected_connected",
        [
            (
                "127.0.0.1:5432",
                "Successfully connected to database server on URI: 127.0.0.1:5432",
                True,
            )
        ],
    )
    @pytest.mark.asyncio
    async def test_connect_to_db(
        self, uri_db_server, expected_log_message, expected_connected, caplog
    ):
        freq_read_data = 5

        app_sensor_reader = AppSensorReader(
            freq_read_data, uri_db_server
        )

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_db()

        assert expected_connected == flag_connected

        # Get the captured log records
        log_records = caplog.records

        # Assert that the log message is captured
        assert any(expected_log_message in record.message for record in log_records)

        # Close connection
        app_sensor_reader.db_client.disconnect()