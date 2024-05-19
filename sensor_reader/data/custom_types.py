import re
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, model_validator

class UrlConstraints(BaseModel):
    """Class model to define generic URLs format parameters."""

    max_length: int = 2083
    allowed_schemes: list = ["nats"]


class NatsUrl(BaseModel):
    """Class model to define NATS URLs."""

    url: str

    @model_validator(mode='after')
    def _validate_format(self):
        constraints = UrlConstraints(max_length=2083, allowed_schemes=["nats"])
        if len(self.url) > constraints.max_length:
            raise ValueError("URL length exceeds max. limit.")

        # Parse the URL to get components
        parsed_url = urlparse(self.url)

        if parsed_url.scheme not in constraints.allowed_schemes:
            raise ValueError("URL header is incorrect. Must be nats://.")

        # Check if there's an IP and port in the netloc
        if ":" in parsed_url.netloc:
            ip, port = parsed_url.netloc.split(":")

            # Validate IP
            ip = ip.strip()
            ip_pattern = re.compile(
                r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            )
            flag_valid_ip = bool(ip_pattern.match(ip) or ip == "localhost")

            if not flag_valid_ip:
                raise ValueError("Invalid IP format.")

            # Validate port
            port = int(port)
            if not (0 <= port <= 65535):
                raise ValueError("Port must be between 0 and 65535.")

            return self
        # If no IP and port are found, raise an error
        raise ValueError("Invalid IP or port.")