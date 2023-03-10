import time

import aiohttp
from loguru import logger


@logger.catch
async def get(url: str, config: dict, data: str = None, retry_time: int = 5):
    async with aiohttp.ClientSession(cookies=config['cookies'], headers={'User-Agent': config['User-Agent']}) \
            as session:
        try:
            if data is None:
                async with session.get(url, proxy=config['proxy']['url'] if config['proxy']['enable'] else None) \
                        as resp:
                    return await resp.read()
            else:
                async with session.post(url, data=data,
                                        proxy=config['proxy']['url'] if config['proxy']['enable'] else None) as resp:
                    return await resp.read()
        except BaseException as e:
            logger.exception(e)
            if retry_time > 0:
                logger.warning(f"Error to download {url}. Retrying. Remaining retry counts: {retry_time}")
                time.sleep(5)
                return await get(url, config, retry_time=retry_time - 1)
            else:
                logger.error(f"Error to download {url}. Will sleep for 60 secs.")
                time.sleep(60)
                return await get(url, config)
