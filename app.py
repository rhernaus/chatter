import argparse
import asyncio
import sys
from typing import Tuple


async def send_data(writer: asyncio.StreamWriter) -> None:
    """Send user input data to the connected node.

    Args:
        writer: StreamWriter object used to send data.
    """
    while True:
        data = await asyncio.get_event_loop().run_in_executor(
            None, input, "Enter the data to send: "
        )
        writer.write(data.encode())
        await writer.drain()
        print(f"Sent: {data}")


async def receive_data(reader: asyncio.StreamReader) -> None:
    """Receive data from the connected node and print it.

    Args:
        reader: StreamReader object used to receive data.
    """
    while True:
        data = await reader.read(100)
        if not data:
            break
        print(f"Received: {data.decode()}")


async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Handle bidirectional data transfer between nodes.

    Args:
        reader: StreamReader object used to receive data.
        writer: StreamWriter object used to send data.
    """
    tasks = [
        asyncio.create_task(send_data(writer)),
        asyncio.create_task(receive_data(reader)),
    ]

    await asyncio.gather(*tasks)


async def listen(host: str, port: int) -> None:
    """Listen for incoming connections and handle them.

    Args:
        host: Host address to listen on.
        port: Port number to listen on.
    """

    async def handle_incoming_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")
        await handle_connection(reader, writer)

    server = await asyncio.start_server(handle_incoming_connection, host, port)
    async with server:
        print(f"Listening on {host}:{port}")
        await server.serve_forever()


async def connect(host: str, port: int) -> None:
    """Connect to a listening node and handle the connection.

    Args:
        host: Host address of the listening node.
        port: Port number of the listening node.
    """
    reader, writer = await asyncio.open_connection(host, port)
    print(f"Connected to {host}:{port}")
    await handle_connection(reader, writer)


async def cancel_all_tasks() -> None:
    """Cancel all running tasks."""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async chat script.")
    parser.add_argument("mode", choices=["listen", "connect"],
                        help="Select operation mode.")
    parser.add_argument("--host", default="localhost",
                        help="Host address (default: localhost)")
    parser.add_argument("--port", type=int, default=12345,
                        help="Port number (default: 12345)")
    args = parser.parse_args()

    try:
        if args.mode == "listen":
            asyncio.run(listen(args.host, args.port))
        elif args.mode == "connect":
            asyncio.run(connect(args.host, args.port))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        asyncio.run(cancel_all_tasks())
        sys.exit(0)
