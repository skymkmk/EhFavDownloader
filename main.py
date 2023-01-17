import asyncio
import datetime
import os.path

import yaml
from loguru import logger

from src import *

if __name__ == '__main__':
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    logger.add(f"./logs/{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')}.log", level="WARNING")
    try:
        with open('./config.yaml', 'r', encoding='UTF-8') as f:
            config = yaml.safe_load(f)
            logger.success('Config loaded.')
    except FileNotFoundError as e:
        logger.error("Can't find config file.")
        exit(1)
    init(config)
    update_data(config)
    asyncio.run(download(config))
    logger.success("Downloaded finished. Program will exit.")
