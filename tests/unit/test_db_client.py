import psycopg2
import pytest
from psycopg2.extensions import connection
from pydantic import ValidationError

from sensor_reader.db.db_client import PostgresDbClient


class TestDbClient:
    @pytest.mark.parametrize(
        "good_uris, bad_uris",
        [
            (
                ["127.0.0.1:1000", "127.0.0.1:2000", "192.168.1.34:3000"],
                ["127.0.0.1:wrong_port", "wrong_ip:5000"],
            )
        ],
    )
    def test_uri_parsing(self, good_uris, bad_uris):
        for good_uri in good_uris:
            PostgresDbClient(good_uri)

        for bad_uri in bad_uris:
            with pytest.raises(ValidationError):
                PostgresDbClient(bad_uri)

    @pytest.mark.parametrize(
        "uri_db_server, expected_connection_type, expected_error_code",
        [
            (
                "127.0.0.1:5432",
                connection,
                None,
            ),
            (
                "192.168.1.27:1000",
                type(None),
                psycopg2.OperationalError,
            ),
        ],
    )
    # @mock.patch.object(psycopg2, "connect")
    def test_connect_to_db(
        self, uri_db_server, expected_connection_type, expected_error_code
    ):
        # mock_db_connect.return_value = connection(), None

        mocked_db_client = PostgresDbClient(uri_db_server)
        db_connection, error_code = mocked_db_client.connect()

        assert type(db_connection) is expected_connection_type
        if expected_error_code is None:
            assert error_code == expected_error_code
        else:
            assert isinstance(error_code, expected_error_code)
