#! /usr/bin/env python3
import asyncio
import datetime
import os.path
import sys

from loguru import logger

from src import *

if __name__ == '__main__':
    args = sys.argv[1:]
    working_dir = os.path.split(__file__)[0]
    if not os.path.exists(os.path.join(working_dir, 'logs')):
        os.mkdir(os.path.join(working_dir, 'logs'))
    logger.add(os.path.join(working_dir, "logs",
                            f"{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')}.log"), level="WARNING")
    init()
    if not ('--download-only' in args or '-d' in args):
        update_data()
    asyncio.run(download())
    logger.success("Downloaded finished. Program will exit.")
