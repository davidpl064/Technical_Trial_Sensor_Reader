import asyncio

import pytest

from sensor_reader.app import AppSensorReader
from tests.command.app_command import send_command


class TestSensorReader:
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
    async def test_action_commands(
        self, uri_message_server, expected_log_message, expected_connected, caplog
    ):
        freq_read_data = 5
        uri_db_server = "127.0.0.1:5432"
        min_range_value = 0
        max_range_value = 10

        app_sensor_reader = AppSensorReader(
            freq_read_data, uri_db_server, min_range_value, max_range_value
        )

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_message_server()

        assert expected_connected == flag_connected

        # Check status is running
        assert app_sensor_reader.flag_on_standby is False

        # Send command to stop reading/publishing data
        await send_command(uri_message_server, "stop")

        # Wait some time for the command to be received and process
        await asyncio.sleep(1)

        # Assert that the log message is captured
        log_records = caplog.records
        assert any(
            "Stopping sensor data capturing and processing." in record.message
            for record in log_records
        )

        # Check app is stopped
        assert app_sensor_reader.flag_on_standby is True

        # Start again
        await send_command(uri_message_server, "start")

        # Assert that the log message is captured
        log_records = caplog.records
        assert any(
            "Restarting sensor data capturing and processing." in record.message
            for record in log_records
        )

        # Wait some time for the command to be received and process
        await asyncio.sleep(1)

        # Check app is running
        assert app_sensor_reader.flag_on_standby is False

        # Exit app
        await send_command(uri_message_server, "exit")

        # Wait some time for the app to be closed
        await asyncio.sleep(15)

        assert app_sensor_reader.flag_on_standby is True
        assert app_sensor_reader.flag_exit is True

        # Assert that the log message is captured
        log_records = caplog.records
        assert any("Closing app ..." in record.message for record in log_records)
