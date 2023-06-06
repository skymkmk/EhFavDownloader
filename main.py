#! /usr/bin/env python3
import asyncio
import datetime
import os.path
import sys

from loguru import logger

import config
import download
import init
import update_metadata

if __name__ == '__main__':
    args = sys.argv[1:]
    if not os.path.exists(os.path.join(config.WORKING_DIR, 'logs')):
        os.mkdir(os.path.join(config.WORKING_DIR, 'logs'))
    logger.add(os.path.join(config.WORKING_DIR, "logs",
                            f"{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')}.log"), level="WARNING")
    init.init()
    if not ('--download-only' in args or '-d' in args):
        update_metadata.update_metadata()
    asyncio.run(download.download())
    logger.success("Downloaded finished. Program will exit.")
