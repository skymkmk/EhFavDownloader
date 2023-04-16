import asyncio
import hashlib
import math
import os
import platform
import re
import sqlite3
import time

import aiohttp
import filetype.filetype
import lxml.etree as etree
from loguru import logger

import src.config
from src.utils import get
from .DownloaderExceptions import Error509
from .config import Config

config = Config()
db_dir = src.config.db_dir
flag = True
retry_times = 3


async def _get_info(gal_info: tuple):
    with sqlite3.connect(db_dir) as conn:
        img_info = conn.execute("SELECT * FROM img WHERE gid = ?", (gal_info[0],)).fetchall()
    if len(img_info) == 0:
        logger.info(f"Getting information for {gal_info[1]}")
        info_flag = True
        url = f"https://{config.website}/g/{gal_info[0]}/{gal_info[3]}"
        while info_flag:
            content = await get(url)
            page = etree.HTML(content)
            if len(page.xpath("//div[@id='gdt']/div[@class='gdtm']")) == 0:
                if len(page.xpath("//div[@id='gdt']/div[@class='gdtl']")) == 0:
                    if len(page.xpath("//div[@class='d']/p[1]")) != 0:
                        logger.warning(page.xpath("//div[@class='d']/p[1]/text()")[0])
                        with sqlite3.connect(db_dir) as conn:
                            conn.execute("UPDATE doujinshi SET status = 2 WHERE gid = ?", (gal_info[0],))
                        return
                    else:
                        logger.error(content)
                        exit(1)
                else:
                    imgs = page.xpath("//div[@id='gdt']/div[@class='gdtl']")
            else:
                imgs = page.xpath("//div[@id='gdt']/div[@class='gdtm']")
            for i in imgs:
                img_info.append(i.xpath('.//a/@href')[0])
            next_gal_list = page.xpath("//div[@class='gtb']//tr/td[last()]/a")
            if len(next_gal_list) == 0:
                info_flag = False
            else:
                url = next_gal_list[0].xpath('./@href')[0]
        img_info = [(re.findall(f"https://{config.website}/s/(\\w*)/.*", value)[0], idx, gal_info[0],)
                    for idx, value in enumerate(img_info)]
        for i in img_info:
            with sqlite3.connect(db_dir) as conn:
                result = conn.execute("SELECT * FROM img WHERE id = ? and page_num = ? and gid = ?",
                                      (i[0], i[1], gal_info[0],)).fetchall()
                if len(result) == 0:
                    conn.execute("INSERT INTO img (id, page_num, gid) VALUES (?, ?, ?)", (i[0], i[1], gal_info[0],))
                    conn.commit()
                else:
                    conn.execute("UPDATE img SET id = ? WHERE page_num = ? and gid = ?", (i[0], i[1], gal_info[0]))
                    conn.commit()
        with sqlite3.connect(db_dir) as conn:
            conn.execute("UPDATE doujinshi SET page_num = ? WHERE gid = ?", (len(img_info), gal_info[0],))
            conn.commit()
        return img_info
    else:
        img_info = [(i[0], i[1], i[2],) for i in img_info if i[3] == 0]
        return img_info


async def _async_download_img(path: str, session: aiohttp.ClientSession, img_info: tuple, gal_name: str,
                              nl: str = None):
    global retry_times
    global flag
    url = f"https://{config.website}/s/{img_info[0]}/{img_info[2]}-{img_info[1] + 1}"
    if nl is not None:
        url += '?nl=' + nl
    while True:
        try:
            async with session.get(url, proxy=config.proxy['url'] if config.proxy['enable'] else None) as resp:
                logger.info(f"Getting information for {gal_name}, page {img_info[1] + 1}")
                content = await resp.text()
            img_page = etree.HTML(content)
            hath_url = img_page.xpath("//img[@id='img']/@src")[0]
            nl = img_page.xpath("//a[@id='loadfail']/@onclick")[0].replace("return nl('", '', 1).replace("')", '', 1)
            async with session.get(hath_url,
                                   proxy=config.proxy['url'] if config.proxy['enable'] else None) as resp:
                logger.info(f"Downloading {gal_name}, page {img_info[1] + 1}")
                img = await resp.read()
                img_hash = hashlib.md5(img).hexdigest()
                if img_hash == '88fe16ae482faddb4cc23df15722348c':
                    raise Error509
            save_path = f"{path}/{img_info[1] + 1:0>8d}.{filetype.filetype.guess_extension(img)}"
            with open(save_path, 'wb') as f:
                f.write(img)
            retry_times = 3
            with sqlite3.connect(db_dir) as conn:
                conn.execute("UPDATE img SET finished = 1, md5 = ? WHERE id = ? and page_num = ? and gid = ?",
                             (img_hash, img_info[0], img_info[1], img_info[2],))
                conn.commit()
            break
        except IndexError:
            logger.error(content)
            flag = False
            break
        except Error509:
            logger.error("Bumped into 509. Will sleep for 20 mins.")
            time.sleep(1200)
            await _async_download_img(path, session, img_info, gal_name)
        except:
            if retry_times > 0:
                logger.warning(f"Error to download {url}. Retrying. Remaining retry counts: {retry_times}")
                retry_times -= 1
                await _async_download_img(path, session, img_info, gal_name, nl)
            else:
                logger.error(f"Error to download {url}. Skip.")
                retry_times = 3
                flag = False


@logger.catch
async def download():
    global flag
    with sqlite3.connect(db_dir) as conn:
        result = conn.execute('SELECT * FROM doujinshi WHERE status = 0').fetchall()
    for i in result:
        with sqlite3.connect(db_dir) as conn:
            category_name = conn.execute('SELECT name FROM category WHERE id = ?', (i[4],)).fetchall()[0][0]
        # Replace the illegal characters
        path = re.sub(r'''[\\/:*?"<>|]''', '', i[1])
        # Limit the folder name length to 255 (bytes for Linux, characters for Windows / macOS) and the path length to
        # 259 characters (Windows) or 1023 bytes (macOS) or 4095 bytes (Linux) due to the limit of file system.
        # Long path extensions supported in Windows 10 1607 and later will not be supported because Windows Explorer
        # does not support long paths and because of compatibility issues.
        path = f"{i[0]}-{path}"
        root = os.path.join(config.save_path, f'{i[4]}-{category_name}')
        os_brand = platform.system()
        if os_brand == 'Windows':
            path_length_limit = 259
        elif os_brand == 'Darwin':
            path_length_limit = 1023
        elif os_brand == 'Linux':
            path_length_limit = 4095
        else:
            path_length_limit = 4095
            # logger.warning(f"Unknown operating system detected. OS name: {os_brand}. There may have some problem when"
            #                f"writing files.")
        if os_brand in ['Windows', 'Darwin']:
            if len(path) > 255:
                path = path[: 255]
        else:
            if len(path.encode()) > 255:
                path = path.encode()[: 255].decode(errors='ignore')
        if os_brand == 'Windows':
            # Because the path does not contain / at the end, here subtract one more. The following is the same as here.
            length_limit = path_length_limit - len(root) - 1
            if len(path) > length_limit:
                path = path[: length_limit]
        else:
            length_limit = path_length_limit - len(root.encode()) - 1
            if len(path.encode()) > length_limit:
                path = path.encode()[: length_limit].decode(errors='ignore')
        path = os.path.join(root, path)
        if not os.path.exists(path):
            os.mkdir(path)
        img_info = await _get_info(i)
        if img_info is not None:
            if len(img_info) != 0:
                async with aiohttp.ClientSession(cookies=config.cookies,
                                                 connector=aiohttp.TCPConnector(limit=config.connect_limit,
                                                                                verify_ssl=False),
                                                 headers={'User-Agent': config.user_agent}) as session:
                    tasks = [asyncio.create_task(_async_download_img(path, session, j, i[1])) for j in img_info]
                    await asyncio.wait(tasks)
            if flag:
                with sqlite3.connect(db_dir) as conn:
                    img_info = conn.execute("SELECT * FROM img WHERE gid = ?", (i[0],)).fetchall()
                if len(img_info) != 0:
                    with open(f"{path}/.ehviewer", 'w') as f:
                        f.write('VERSION2\n')
                        f.write('00000000\n')
                        f.write(str(i[0]) + '\n')
                        f.write(i[3] + '\n')
                        f.write('1\n')
                        f.write(str(math.ceil(len(img_info) / 40)) + '\n')
                        if len(img_info) < 40:
                            f.write(str(len(img_info)) + '\n')
                        else:
                            f.write('40\n')
                        f.write(str(len(img_info)) + '\n')
                        with sqlite3.connect(db_dir) as conn:
                            result = conn.execute("SELECT page_num, id FROM img WHERE gid = ?", (i[0],)).fetchall()
                        result.sort(key=lambda x: x[0])
                        for j in result:
                            f.write(f"{j[0]} {j[1]}\n")
                    with sqlite3.connect(db_dir) as conn:
                        conn.execute("UPDATE doujinshi SET finished = 1 WHERE gid = ?", (i[0],))
                        conn.commit()
                    logger.success(f"Gallery {i[0]} {i[1]} download finished.")
            flag = True
