import asyncio

from loguru import logger

import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

from sensor_reader.data.custom_types import NatsUrl

class NATSClient():
    def __init__(self, uri_nats_server: str):
        self.uri_server = NatsUrl(url=uri_nats_server)

    async def connect_to_server(self):
        # Connect to local NATS server
        self.nats_client = await nats.connect(self.uri_server)

        logger.info("Successfully connected to NATS server on URI: {}")

        async def message_handler(msg):
            subject = msg.subject
            reply = msg.reply
            data = msg.data.decode()
            print(f"Received a message on '{subject}': {data}")

            # Respond to the message if needed
            if reply:
                await nc.publish(reply, b'OK')

        # Subscribe to a topic
        await nc.subscribe("foo", cb=message_handler)

        # Publish a message to the topic
        await nc.publish("foo", b'Hello World')

        # Keep the connection open to listen for messages
        await asyncio.sleep(10)

        # Close the connection
        await nc.close()

    async def disconnect_from_server(self):
        # Terminate connection to NATS.
        await self.nats_client.drain()