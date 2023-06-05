import time

import aiohttp
from loguru import logger

import config


async def get(url: str, data: str = None, retry_time: int = config.retry_time,
              ultimate_retry_time: int = config.retry_time) -> bytes:
    async with aiohttp.ClientSession(cookies=config.cookies, headers={'User-Agent': config.user_agent}) \
            as session:
        try:
            if data is None:
                async with session.get(url, proxy=config.proxy['url'] if config.proxy['enable'] else None) \
                        as resp:
                    return await resp.read()
            else:
                async with session.post(url, data=data,
                                        proxy=config.proxy['url'] if config.proxy['enable'] else None) as resp:
                    return await resp.read()
        except BaseException as e:
            if retry_time > 0:
                logger.warning(f"Error to connect {url}. Retrying. Remaining retry counts: {retry_time}")
                time.sleep(5)
                return await get(url, data=data, retry_time=retry_time - 1, ultimate_retry_time=ultimate_retry_time)
            else:
                if ultimate_retry_time > 0:
                    logger.warning(f"Error to connect {url}. Will sleep for 60 secs.")
                    time.sleep(60)
                    return await get(url, data=data, ultimate_retry_time=ultimate_retry_time - 1)
                else:
                    logger.error(f"Error to connect {url}. Skip it.")
