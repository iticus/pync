#!/usr/bin/env python3
"""
Created on 2026-01-17

@author: iticus
"""

import asyncio
import signal
import os
import sys

from pathlib import Path


def handler(signum, frame):
    print(f"interrupt: {signum}, {frame}")
    sys.exit()


def load_env(path: str):
    with open(path, "r") as f:
        for line in f.readlines():
            if line.strip().startswith("#"):
                continue
            key, value = line.strip().split("=")
            os.environ[key] = value


async def tcp_client(host: str, port: int):
    reader, writer = await asyncio.open_connection(host, port)
    print("opened")
    if port == 6379:  # handle Redis auth automatically
        redis_user = os.getenv("REDISCLI_USER", "default")
        redis_pwd = os.getenv("REDISCLI_AUTH", "")
        message = f"auth {redis_user} {redis_pwd}\n"
        writer.write(message.encode())
        await writer.drain()
        data = await reader.read(100)
        print(data.decode())
    while True:
        try:
            message = input()
        except EOFError:
            break
        data = message + "\n"
        writer.write(data.encode())
        await writer.drain()
        data = await reader.read(256 * 256)
        if message.lower().strip() == "quit" and data == b"+OK\r\n":
            break
        print(data.decode())
    print("closing connection")
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    config = Path.home() / ".pync"
    if config.is_file():
        load_env(config)
    if len(sys.argv) < 3:
        sys.exit("provide host and port values")
    if not sys.argv[2].isdigit():
        sys.exit("provide valid port value")
    host, port = sys.argv[1], int(sys.argv[2])
    asyncio.run(tcp_client(host, port))
