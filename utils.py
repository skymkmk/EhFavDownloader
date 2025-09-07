__all__ = ['get', 'truncate_path', 'Error509', 'FailToDownloadIMG']

import asyncio
import os
import platform
import re
import time
from typing import Union
from weakref import WeakKeyDictionary

import httpx
from loguru import logger

import config

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-ZA,en;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}

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
ILLEGAL_NAME = re.compile(r'''[\\/:*?"<>|]''')


class Error509(BaseException):
    pass


class FailToDownloadIMG(BaseException):
    pass

_clients: WeakKeyDictionary = WeakKeyDictionary()

async def _get_client() -> httpx.AsyncClient:
    loop = asyncio.get_running_loop()
    
    if loop not in _clients:
        _clients[loop] = httpx.AsyncClient(
            cookies=config.cookies,
            headers=headers,
        )
    
    return _clients[loop]

async def get(url: str, data: str = None, retry_time: int = 0,
              ultimate_retry_time: int = 0) -> Union[bytes, None]:
    client = await _get_client()
    try:
        if data is None:
            resp = await client.get(url)
        else:
            resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.content
    except BaseException:
        if retry_time > 0:
            print(f"Error to connect {url}. Retrying. Remaining retry counts: {retry_time}")
            await asyncio.sleep(5)
            return await get(url, data=data, retry_time=retry_time - 1, ultimate_retry_time=ultimate_retry_time)
        else:
            if ultimate_retry_time > 0:
                print(f"Error to connect {url}. Will sleep for 60 secs.")
                await asyncio.sleep(60)
                return await get(url, data=data, ultimate_retry_time=ultimate_retry_time - 1)
            else:
                print(f"Error to connect {url}. Skip it.")
                return None

def truncate_path(root: str, file_name: str, spare_limit: int = 10) -> str:
    file_name = ILLEGAL_NAME.sub('', file_name)
    if os_brand in ['Windows', 'Darwin']:
        if len(file_name) > FILE_NAME_LENGTH_LIMIT - spare_limit:
            file_name = file_name[:FILE_NAME_LENGTH_LIMIT - spare_limit]
    elif len(file_name.encode(encoding='utf-8')) > FILE_NAME_LENGTH_LIMIT - spare_limit:
        file_name = file_name.encode(encoding='utf-8')[: FILE_NAME_LENGTH_LIMIT - spare_limit].decode(encoding='utf-8',
                                                                                                      errors='ignore')
    if os_brand == 'Windows':
        # Because the path does not contain / at the end, here subtract one more. The following is the same as here.
        length_limit = PATH_LENGTH_LIMIT - len(root) - 1 - spare_limit
        if len(file_name) > length_limit:
            file_name = file_name[: length_limit]
    else:
        length_limit = PATH_LENGTH_LIMIT - len(root.encode(encoding='utf-8')) - 1 - spare_limit
        if len(file_name.encode(encoding='utf-8')) > length_limit:
            file_name = file_name.encode(encoding='utf-8')[: length_limit].decode(encoding='utf-8', errors='ignore')
    return os.path.join(root, file_name)
