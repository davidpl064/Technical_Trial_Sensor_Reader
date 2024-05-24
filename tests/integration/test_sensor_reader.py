import asyncio
from unittest import mock

import numpy as np
import pytest
from nats.aio.msg import Msg

from sensor_reader.app import AppSensorReader
from tests.command.app_command import send_command
from tests.mocks.sensor_infrared import SensorInfrared


class Helpers:
    async def handle_published_data(self, msg: Msg):
        self.data = msg.data.decode()


@pytest.fixture
def helpers():
    return Helpers()


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

        app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)

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
        await asyncio.sleep(10)

        assert app_sensor_reader.flag_on_standby is True
        assert app_sensor_reader.flag_exit is True

        # Assert that the log message is captured
        log_records = caplog.records
        assert any("Closing app ..." in record.message for record in log_records)

    @pytest.mark.parametrize(
        "uri_message_server, raw_sensor_data, expected_log_message, expected_connected",
        [
            (
                "nats://localhost:4222",
                np.array([1, 2, 3, 4]),
                "Successfully connected to NATS server on URI: nats://localhost:4222",
                True,
            )
        ],
    )
    @pytest.mark.asyncio
    @mock.patch("sensor_reader.app.AppSensorReader.handler_raw_data_messages")
    async def test_raw_data_from_sensor(
        self,
        handler_raw_data_mock,
        uri_message_server,
        raw_sensor_data,
        expected_log_message,
        expected_connected,
        caplog,
    ):
        freq_read_data = 5
        uri_db_server = "127.0.0.1:5432"
        min_range_value = 0
        max_range_value = 10

        app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_message_server()

        assert expected_connected == flag_connected

        # Assert that the log message is captured
        log_records = caplog.records
        assert any(expected_log_message in record.message for record in log_records)

        # app_sensor_reader.handler_raw_data_messages = mock.MagicMock()

        # Mock input sensor data
        mock_sensor = SensorInfrared(
            min_range_value, max_range_value, uri_message_server
        )
        await mock_sensor.connect_to_message_server()
        mock_sensor._last_data = raw_sensor_data
        await mock_sensor.publish_data()

        await asyncio.sleep(1)

        # Check data was received and has good format
        handler_raw_data_mock.assert_called_once()

        # Disconnect and exit
        await app_sensor_reader.disconnect_from_message_server()
        await asyncio.sleep(10)

    @pytest.mark.parametrize(
        "uri_message_server, raw_sensor_data, expected_log_message, expected_connected",
        [
            (
                "nats://localhost:4222",
                np.array([1, 2, 3, 4]),
                "Successfully connected to NATS server on URI: nats://localhost:4222",
                True,
            )
        ],
    )
    @pytest.mark.asyncio
    async def test_read_data_from_sensor(
        self,
        uri_message_server,
        raw_sensor_data,
        expected_log_message,
        expected_connected,
        caplog,
    ):
        freq_read_data = 5
        uri_db_server = "127.0.0.1:5432"
        min_range_value = 0
        max_range_value = 10

        app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_message_server()

        assert expected_connected == flag_connected

        # Assert that the log message is captured
        log_records = caplog.records
        assert any(expected_log_message in record.message for record in log_records)

        # Mock input sensor data
        mock_sensor = SensorInfrared(
            min_range_value, max_range_value, uri_message_server
        )
        await mock_sensor.connect_to_message_server()
        mock_sensor._last_data = raw_sensor_data
        await mock_sensor.publish_data()

        await asyncio.sleep(1)

        # Check data was received and has good format
        assert len(app_sensor_reader.last_sensor_data) == len(raw_sensor_data)

        # Disconnect and exit
        await app_sensor_reader.disconnect_from_message_server()
        await asyncio.sleep(5)

    @pytest.mark.parametrize(
        "uri_message_server, raw_sensor_data, expected_log_message, expected_connected",
        [
            (
                "nats://localhost:4222",
                np.array([1, 2, 3, 4]),
                "Successfully connected to NATS server on URI: nats://localhost:4222",
                True,
            )
        ],
    )
    @pytest.mark.asyncio
    async def test_publishing_data(
        self,
        uri_message_server,
        raw_sensor_data,
        expected_log_message,
        expected_connected,
        caplog,
        helpers,
    ):
        freq_read_data = 5
        uri_db_server = "127.0.0.1:5432"
        min_range_value = 0
        max_range_value = 10

        app_sensor_reader = AppSensorReader(freq_read_data, uri_db_server)

        # Connect to NATS server
        flag_connected = await app_sensor_reader.connect_to_message_server()

        assert expected_connected == flag_connected

        # Assert that the log message is captured
        log_records = caplog.records
        assert any(expected_log_message in record.message for record in log_records)

        # Mock input sensor data
        mock_sensor = SensorInfrared(
            min_range_value, max_range_value, uri_message_server
        )
        await mock_sensor.connect_to_message_server()
        mock_sensor._last_data = raw_sensor_data
        await mock_sensor.publish_data()

        await asyncio.sleep(1)

        # Publish data to "publishing" topic
        sub_publishing = await app_sensor_reader.nats_client.subscribe(
            app_sensor_reader.topic_publishing, cb=helpers.handle_published_data
        )
        await app_sensor_reader.publish_sensor_data(app_sensor_reader.last_sensor_data)

        await asyncio.sleep(1)
        assert helpers.data == str(app_sensor_reader.last_sensor_data)

        # Unsubscribe publishing topic
        await sub_publishing.unsubscribe()

        # Disconnect and exit
        await app_sensor_reader.disconnect_from_message_server()
        await asyncio.sleep(5)
