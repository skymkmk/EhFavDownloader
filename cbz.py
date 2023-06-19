import datetime
import os.path
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from typing import List

from loguru import logger

import config
import sql

VERIFY_ID = re.compile(r"(\d+)-.*")


def _get_dir(root: str) -> List[str]:
    save_dir = [os.path.join(root, i) for i in os.listdir(root) if os.path.isdir(os.path.join(root, i))]
    return_dir = []
    for i in save_dir:
        try:
            the_id = int(VERIFY_ID.findall(os.path.split(i)[-1])[0])
            if root == config.save_path:
                if the_id < 1 or the_id > 10:
                    continue
            return_dir.append(i)
        except IndexError:
            pass
    return return_dir


def config_info_xml(gid: int, path: str) -> None:
    gtoken, title, artist, publisher, tag, language, favorited_time = sql.select_gallery_metadata(gid)
    root = ET.Element("ComicInfo")
    if favorited_time is not None:
        favorited_time = datetime.datetime.strptime(favorited_time, "%Y-%m-%d %H:%M")
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
    web_node.text = f"https://{config.website}/g/{gid}/{gtoken}"
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


def update_cbz() -> None:
    category_dir = _get_dir(config.save_path)
    for i in category_dir:
        logger.info(f"Updating {os.path.split(i)[-1]}")
        doujinshi_dir = _get_dir(i)
        for j in doujinshi_dir:
            for k in os.listdir(j):
                if os.path.splitext(k)[-1] == '.cbz':
                    try:
                        gid = VERIFY_ID.findall(k)[0]
                        result = sql.select_gallery_metadata(gid)
                        if len(result) == 0:
                            continue
                        logger.info(f"Updating {os.path.split(j)[-1]}")
                        with tempfile.TemporaryDirectory() as tempdir:
                            with zipfile.ZipFile(os.path.join(j, k), 'r') as zf:
                                zf.extractall(tempdir)
                            config_info_xml(gid, tempdir)
                            with zipfile.ZipFile(os.path.join(j, os.path.splitext(k)[0] + '.tmp'), 'w') as zf:
                                for m in os.listdir(tempdir):
                                    zf.write(os.path.join(tempdir, m), m)
                        # To prevent operations from failing due to interruptions.
                        while True:
                            try:
                                try:
                                    os.remove(os.path.join(j, k))
                                except FileNotFoundError:
                                    pass
                                os.rename(os.path.join(j, os.path.splitext(k)[0] + '.tmp'), os.path.join(j, k))
                                break
                            except KeyboardInterrupt:
                                pass
                        logger.success(f"{os.path.split(j)[-1]} updated")
                    except IndexError:
                        pass
    logger.success("CBZ updated.")
