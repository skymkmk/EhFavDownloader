#! /usr/bin/env python3
import asyncio
import datetime
import os.path

from loguru import logger

from src import *

if __name__ == '__main__':
    working_dir = os.path.split(__file__)[0]
    if not os.path.exists(os.path.join(working_dir, 'logs')):
        os.mkdir(os.path.join(working_dir, 'logs'))
    logger.add(os.path.join(working_dir, "logs",
                            f"{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')}.log"), level="WARNING")
    init()
    update_data()
    asyncio.run(download())
    logger.success("Downloaded finished. Program will exit.")
