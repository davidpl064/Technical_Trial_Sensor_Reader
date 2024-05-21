import argparse
import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

async def main(args):
    nats_client = await nats.connect(args.uri_nats_server)

    match args.app_command:
        case "start":
            app_command = 0
        case "stop":
            app_command = 1
        case "exit":
            app_command = 2

    await nats_client.publish("app_command", str(app_command).encode())
    await nats_client.drain()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("app_command", type=str, help="Root directory of the dataset")
    parser.add_argument(
        "--uri_nats_server",
        type=str,
        help="URI of NATS server",
        required=False,
        default="nats://localhost:4222",
    )
    args = parser.parse_args()
    asyncio.run(main(args))