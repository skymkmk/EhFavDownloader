__all__ = ['get', 'truncate_path']

import os
import platform
import time
from typing import Union

import aiohttp
from loguru import logger

import config

# Limit the folder name length to 255 (bytes for Linux, characters for Windows / macOS) and the path length to
# 259 characters (Windows) or 1023 bytes (macOS) or 4095 bytes (Linux) due to the limit of file system.
# Long path extensions supported in Windows 10 1607 and later will not be supported because Windows Explorer
# does not support long paths and because of compatibility issues.
os_brand = platform.system()
if os_brand == 'Windows':
    PATH_LENGTH_LIMIT = 259
elif os_brand == 'Darwin':
    PATH_LENGTH_LIMIT = 1023
elif os_brand == 'Linux':
    PATH_LENGTH_LIMIT = 4095
else:
    PATH_LENGTH_LIMIT = 4095
FILE_NAME_LENGTH_LIMIT = 255


class Error509(BaseException):
    pass


class FailToDownloadIMG(BaseException):
    pass


async def get(url: str, data: str = None, retry_time: int = config.retry_time,
              ultimate_retry_time: int = config.retry_time) -> Union[bytes, None]:
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
        except BaseException:
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
                    return


def truncate_path(root: str, file_name: str) -> str:
    if os_brand in ['Windows', 'Darwin']:
        if len(file_name) > FILE_NAME_LENGTH_LIMIT:
            file_name = file_name[:FILE_NAME_LENGTH_LIMIT]
    elif len(file_name.encode(encoding='utf-8')) > FILE_NAME_LENGTH_LIMIT:
        file_name = file_name.encode(encoding='utf-8')[: FILE_NAME_LENGTH_LIMIT].decode(encoding='utf-8',
                                                                                        errors='ignore')
    if os_brand == 'Windows':
        # Because the path does not contain / at the end, here subtract one more. The following is the same as here.
        length_limit = PATH_LENGTH_LIMIT - len(root) - 1
        if len(file_name) > length_limit:
            file_name = file_name[: length_limit]
    else:
        length_limit = PATH_LENGTH_LIMIT - len(root.encode(encoding='utf-8')) - 1
        if len(file_name.encode(encoding='utf-8')) > length_limit:
            file_name = file_name.encode(encoding='utf-8')[: length_limit].decode(encoding='utf-8', errors='ignore')
    return os.path.join(root, file_name)
