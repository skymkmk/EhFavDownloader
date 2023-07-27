import asyncio
import hashlib
import os
import sys
import zipfile
from typing import Union, List, Tuple

import filetype.filetype
from loguru import logger

import cbz
import config
import exitcodes
import pageparser
import sql
import utils
from utils import *

HASH509 = '88fe16ae482faddb4cc23df15722348c'


async def _get_info(gal_info: Tuple[int, str, int, str, int]) -> Union[List[Tuple[int, str]], None]:
    img_count = sql.select_img_counts(gal_info[0])
    if img_count != gal_info[2]:
        logger.info(f"Getting information for {gal_info[3]}")
        url = f"https://{config.website}/g/{gal_info[0]}/{gal_info[1]}"
        img_info = await pageparser.parse_gallery_img_list(url)
        if img_info is None:
            sql.update_doujinshi_as_dmca(gal_info[0])
            return
        for idx, ptoken in enumerate(img_info):
            ptoken = ptoken[0]
            sql.update_img_info(ptoken, idx, gal_info[0])
    img_info = sql.select_img_info(gal_info[0])
    return img_info


async def _download_img(sem: asyncio.Semaphore, path: str, gid: int, page_num: int, ptoken: str, gal_name: str,
                        nl: str = None, retry_time: int = config.retry_time) -> bool:
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
        return True
    except Error509:
        logger.error("Bumped into 509.")
        exit(exitcodes.BUMPED_509)
    except FailToDownloadIMG:
        if retry_time > 0:
            logger.warning(f"Error to download {url}. Retrying. Remaining retry counts: {retry_time}")
            sem.release()
            return await _download_img(sem, path, gid, page_num, ptoken, gal_name, nl, retry_time - 1)
        else:
            logger.error(f"Error to download {url}. Skip.")
            sem.release()
            return False


def _detect_cbz(root: str, gid: int) -> bool:
    matched_dir = [os.path.join(root, i) for i in os.listdir(root) if str(gid) in i]
    if len(matched_dir) == 0:
        return False
    elif len(matched_dir) > 1:
        logger.error(f"Detected multi path for {gid} in {root}. Plz deal with it.")
        exit(exitcodes.MULTI_GID_IN_DL_DIR_DETECTED)
    else:
        matched_dir = matched_dir[0]
        cbzs = [os.path.join(matched_dir, i) for i in os.listdir(matched_dir) if '.cbz' in i and str(gid) in i]
        if len(cbzs) == 0:
            return False
        elif len(cbzs) > 1:
            logger.error(f"Detected multi cbz in {matched_dir}. Plz deal with it.")
            exit(exitcodes.MULTI_CBZ_IN_DL_DIR_DETECTED)
        else:
            if os.stat(cbzs[0]).st_size > 102400:
                return True
            else:
                return False


async def download() -> None:
    gal_info = sql.select_doujinshi_for_download()
    for i in gal_info:
        category_name = sql.select_category_name(i[4])
        root = os.path.join(config.save_path, f'{i[4]}-{category_name}')
        # Recover download.
        if config.save_as_cbz:
            detected = _detect_cbz(root, i[0])
            if detected:
                args = sys.argv[1:]
                if '--just-detect-cbz' in args:
                    skip_cbz = True
                else:
                    while True:
                        option = input(f"{i[3]} cbz file detected, do you wanna skip it? [N/y]: ")
                        if option in ['Y', 'y']:
                            skip_cbz = True
                            break
                        elif option in ['N', 'n']:
                            skip_cbz = False
                            break
                if skip_cbz:
                    sql.update_gallery_success(i[0])
                    logger.info(f"Skip {i[3]}")
                    continue
        # Replace the illegal characters
        path = f"{i[0]}-{i[3]}"
        path = truncate_path(root, path)
        if not os.path.exists(path):
            os.mkdir(path)
        img_info = await _get_info(i)
        if img_info is not None:
            if len(img_info) != 0:
                sem = asyncio.Semaphore(config.connect_limit)
                tasks = [_download_img(sem, path, i[0], j[0], j[1], i[3]) for j in img_info]
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
                    cbz.config_info_xml(i[0], path)
                    file_list = [os.path.join(path, j) for j in os.listdir(path)
                                 if os.path.isfile(os.path.join(path, j))]
                    with zipfile.ZipFile(file_path, 'w') as zf:
                        for file in file_list:
                            zf.write(file, os.path.split(file)[-1])
                    sql.update_gallery_success(i[0])
                    for j in file_list:
                        os.remove(j)
                else:
                    sql.update_gallery_success(i[0])
                logger.success(f"Gallery {i[0]} {i[3]} download finished.")
