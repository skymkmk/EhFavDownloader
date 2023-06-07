import asyncio
import datetime
import hashlib
import os
import time
import xml.etree.ElementTree as ET
import zipfile
from typing import Union, List, Tuple

import filetype.filetype
from loguru import logger

import config
import pageparser
import sql
import utils
from utils import *

HASH509 = '88fe16ae482faddb4cc23df15722348c'
sem = asyncio.Semaphore(config.connect_limit)


async def _get_info(gal_info: Tuple[int, str, int, str, int]) -> Union[List[Tuple[str]], None]:
    img_count = sql.select_img_counts(gal_info[0])
    if img_count != gal_info[2]:
        logger.info(f"Getting information for {gal_info[3]}")
        url = f"https://{config.website}/g/{gal_info[0]}/{gal_info[1]}"
        img_info = await pageparser.parse_gallery_img_list(url)
        if img_info is None:
            sql.update_doujinshi_as_dmca(gal_info[0])
        for idx, ptoken in enumerate(img_info):
            ptoken = ptoken[0]
            sql.update_img_info(ptoken, idx, gal_info[0])
    img_info = sql.select_img_info(gal_info[0])
    return img_info


async def _download_img(path: str, gid: int, page_num: int, ptoken: str, gal_name: str, nl: str = None,
                        retry_time: int = config.retry_time) -> bool:
    await sem.acquire()
    url = f"https://{config.website}/s/{ptoken}/{gid}-{page_num + 1}"
    if nl is not None:
        url += '?nl=' + nl
    try:
        logger.info(f"Catch the origin url for {gal_name}, page {page_num + 1}")
        page = await get(url)
        origin_url, nl = pageparser.parse_original_img_url(page)
        logger.info(f"Downloading {gal_name}, page {page_num + 1}")
        img = await get(origin_url, retry_time=0, ultimate_retry_time=0)
        if img is None:
            raise FailToDownloadIMG
        img_hash = hashlib.md5(img).hexdigest()
        if img_hash == HASH509:
            raise Error509
        save_path = os.path.join(path, f"{page_num + 1:0>8d}.{filetype.filetype.guess_extension(img)}")
        with open(save_path, 'wb') as f:
            f.write(img)
        sql.update_img_success(gid, ptoken, img_hash)
        sem.release()
    except Error509:
        logger.error("Bumped into 509. Will sleep for 20 mins.")
        time.sleep(1200)
        sem.release()
        await _download_img(path, gid, page_num, ptoken, gal_name, nl)
    except FailToDownloadIMG:
        if retry_time > 0:
            logger.warning(f"Error to download {url}. Retrying. Remaining retry counts: {retry_time}")
            sem.release()
            await _download_img(path, gid, page_num, ptoken, gal_name, nl, retry_time - 1)
        else:
            logger.error(f"Error to download {url}. Skip.")
            sem.release()
            return False
    return True


async def download() -> None:
    gal_info = sql.select_doujinshi_for_download()
    for i in gal_info:
        category_name = sql.select_category_name(i[4])
        # Replace the illegal characters
        path = f"{i[0]}-{i[3]}"
        root = os.path.join(config.save_path, f'{i[4]}-{category_name}')
        path = truncate_path(root, path)
        if not os.path.exists(path):
            os.mkdir(path)
        img_info = await _get_info(i)
        if img_info is not None:
            if len(img_info) != 0:
                tasks = [asyncio.create_task(_download_img(path, i[0], j[0], j[1], i[3])) for j in img_info]
                success = await asyncio.gather(*tasks)
                success = set(success)
                if False in success:
                    success = False
                else:
                    success = True
            else:
                success = True
            if success:
                if config.save_as_cbz:
                    logger.info(f"Saving {i[0]} {i[3]} as cbz...")
                    title, artist, publisher, tag, language, favorited_time = sql.select_gallery_metadata(i[0])
                    favorited_time = datetime.datetime.strptime(favorited_time, "%Y-%m-%d %H:%M")
                    root = ET.Element("ComicInfo")
                    year_node = ET.SubElement(root, "Year")
                    year_node.text = str(favorited_time.year)
                    month_node = ET.SubElement(root, 'Month')
                    month_node.text = str(favorited_time.month)
                    day_node = ET.SubElement(root, "Day")
                    day_node.text = str(favorited_time.day)
                    title_node = ET.SubElement(root, "Title")
                    title_node.text = title
                    artist_node = ET.SubElement(root, "Writer")
                    artist_node.text = artist
                    web_node = ET.SubElement(root, "Web")
                    web_node.text = f"https://{config.website}/g/{i[0]}/{i[1]}"
                    series_node = ET.SubElement(root, "Series")
                    series_node.text = title
                    agerating_node = ET.SubElement(root, "AgeRating")
                    agerating_node.text = "R18+"
                    publisher_node = ET.SubElement(root, "Publisher")
                    publisher_node.text = publisher
                    mange_node = ET.SubElement(root, "Manga")
                    mange_node.text = "YesAndRightToLeft"
                    tag_node = ET.SubElement(root, "Tags")
                    tag_node.text = tag
                    language_node = ET.SubElement(root, "LanguageISO")
                    language_node.text = language
                    tree = ET.ElementTree(root)
                    tree.write(os.path.join(path, "ComicInfo.xml"), encoding='utf-8')
                    file_list = [os.path.join(path, j) for j in os.listdir(path)
                                 if os.path.isfile(os.path.join(path, j))]
                    save_path = utils.truncate_path(path, f"{i[0]}-{title}", spare_limit=4)
                    save_path += '.cbz'
                    with zipfile.ZipFile(save_path, 'w') as zf:
                        for file in file_list:
                            zf.write(file, os.path.split(file)[-1])
                    sql.update_gallery_success(i[0])
                    for j in file_list:
                        os.remove(j)
                else:
                    sql.update_gallery_success(i[0])
                logger.success(f"Gallery {i[0]} {i[3]} download finished.")
