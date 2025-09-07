__all__ = ['parse_fav_category_list', 'is_displayed_as_minimal',
           'parse_fav_galleries_list', 'parse_gallery_img_list', 'parse_original_img_url']

import re
from typing import List, Tuple, Union

import lxml.html as lhtml
from loguru import logger

import time
import config
import exitcodes
from utils import get

CATEGORY_XPATH = "//div[@class='nosel']/div[@class='fp']"
CATEGORY_NODE_XPATH = "./div[3]/text()"
FAV_ORDER_XPATH = "//div[@id='ujumpbox']/../div[1]//option[@selected]/@value"
FAV_DISPLAY_XPATH = "//div[@id='ujumpbox']/../div[last()]//option[@selected]/@value"
FAV_GALLERY_EMPTY_XPATH = "//div[@class='ido']/p/text()"
FAV_GALLERY_XPATH = "//form[@id='favform']//tr[position() > 1]"
FAV_GALLERY_URL_XPATH = "./td[contains(@class, 'glname')]/a/@href"
FAV_GALLERY_DATE_XPATH = "./td[contains(@class, 'glfav')]/text()"
FAV_GALLERY_NEXT_URL_XPATH = "//a[@id='dnext']/@href"
IMG_LIST_XPATH = "//div[@id='gdt']//a/@href"
GALLERY_NOTICE_XPATH = "//div[@class='d']/p[1]/text()"
GALLERY_NEXT_PAGE_XPATH = "//div[@class='gtb']//tr/td[last()]/a/@href"
IMG_ORIGINAL_URL_XPATH = "//img[@id='img']/@src"
IMG_NL_XPATH = "//a[@id='loadfail']/@onclick"
SEARCH_FAV_LIST_NODE = re.compile(f"^https://{config.website}/g/(\\d+)/(\\w+)")
SEARCH_PTOKEN = re.compile(f"^https://{config.website}/s/(\\w+)/.*")
SEARCH_NL = re.compile(r"nl\('([\w\-]+)'\)")


def parse_fav_category_list(page: bytes) -> List[str]:
    html = lhtml.fromstring(page)
    categories_node = html.xpath(CATEGORY_XPATH)
    if len(categories_node) == 0:
        logger.error(page.decode(encoding="UTF-8", errors="ignore"))
        exit(exitcodes.CANT_PARSE_FAV_CATEGORY)
    categories = []
    for i in categories_node:
        categories.append(i.xpath(CATEGORY_NODE_XPATH)[0])
    return categories


def is_displayed_as_minimal(page: bytes) -> bool:
    html = lhtml.fromstring(page)
    display = html.xpath(FAV_DISPLAY_XPATH)
    if len(display) == 0:
        return True
    return display[0] == 'm'


def parse_fav_galleries_list(page: bytes) -> Union[Tuple[List[Tuple[int, str, str]], Union[str, None]], None]:
    html = lhtml.fromstring(page)
    node_list = html.xpath(FAV_GALLERY_XPATH)
    if len(node_list) == 0:
        notice = html.xpath(FAV_GALLERY_EMPTY_XPATH)
        if len(notice) == 0:
            logger.error(page.decode(encoding="UTF-8", errors="ignore"))
            exit(exitcodes.CANT_PARSE_FAV_LIST)
        logger.info(notice[0])
        return
    lists = []
    for i in node_list:
        gtoken: str
        gid, gtoken = SEARCH_FAV_LIST_NODE.findall(i.xpath(FAV_GALLERY_URL_XPATH)[0])[0]
        gid = int(gid)
        date = i.xpath(FAV_GALLERY_DATE_XPATH)[0]
        lists.append((gid, gtoken, date))
    next_url = html.xpath(FAV_GALLERY_NEXT_URL_XPATH)
    if len(next_url) == 0:
        return lists, None
    else:
        return lists, next_url[0]


async def parse_gallery_img_list(url: str, img_list: Union[List[Tuple[str]], None] = None) -> Union[
    List[Tuple[str]], None]:
    if img_list is None:
        img_list = []
    page = await get(url)
    html = lhtml.fromstring(page)
    the_list = html.xpath(IMG_LIST_XPATH)
    if len(the_list) == 0:
        notice = html.xpath(GALLERY_NOTICE_XPATH)
        if len(notice) == 0:
            logger.error(page.decode(encoding="UTF-8", errors="ignore"))
            exit(exitcodes.CANT_PARSE_GALLERY)
        logger.error(notice)
        return
    for i in the_list:
        img_list.append((SEARCH_PTOKEN.findall(i)[0],))
    next_page = html.xpath(GALLERY_NEXT_PAGE_XPATH)
    if len(next_page) != 0:
        await parse_gallery_img_list(next_page[0], img_list=img_list)
    return img_list


def parse_original_img_url(page: bytes, retry=3) -> Tuple[str, str]:
    html = lhtml.fromstring(page)
    original_url = html.xpath(IMG_ORIGINAL_URL_XPATH)
    nl = html.xpath(IMG_NL_XPATH)
    if len(original_url) == 0 or len(nl) == 0:
        if retry > 0:
            time.sleep(3)
            logger.warning(f"retry original {retry}")
            return parse_original_img_url(page, retry - 1)
        else:
            logger.error("Error to parse img page. Please contact skymkmk for more information.")
            print(page)
            exit(exitcodes.CANT_PARSE_IMG_PAGE)
    return original_url[0], SEARCH_NL.findall(nl[0])[0]
