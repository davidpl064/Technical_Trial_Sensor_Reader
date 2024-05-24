import pytest
from pydantic import ValidationError

from sensor_reader.data.custom_types import NatsUrl


class TestNatsUrls:
    @pytest.mark.parametrize(
        "good_uris, bad_uris",
        [
            (
                [
                    "nats://localhost:4222",
                    "nats://localhost:6000",
                    "nats://127.0.0.50:4222",
                ],
                [
                    "https://localhost:4222",
                    "nats://wrong_ip:5000",
                    "nats://127.0.0.1:-5",
                ],
            )
        ],
    )
    def test_url_parsing(self, good_uris, bad_uris):
        for good_uri in good_uris:
            NatsUrl(url=good_uri)

        for bad_uri in bad_uris:
            with pytest.raises(ValidationError):
                NatsUrl(url=bad_uri)
