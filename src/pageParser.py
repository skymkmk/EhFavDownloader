import re

from .config import Config
from loguru import logger
from lxml.etree import HTML

_config = Config()
def fav_category(text: bytes) -> list:
    page = HTML(text)
    result = []
    categories = page.xpath("//div[@class='nosel']/div[@class='fp']")
    if len(categories) == 0:
        logger.error(text.decode())
        exit(1)
    for idx, node in enumerate(categories):
        result.append([idx + 1, node.xpath('./div[3]/text()')[0]])
    return result


def fav_page(text: bytes):
    page = HTML(text)
    urls = page.xpath("//form[@id='favform']/table/tr//td[contains(@class, 'glname')]/a/@href")
    fav_time = page.xpath("//form[@id='favform']/table/tr//td[contains(@class, 'glfav')]/text()")
    if len(urls) == 0:
        notice = page.xpath("//div[@class='ido']/p/text()")
        if len(notice) != 1:
            logger.error(text.decode())
            exit(1)
        else:
            return notice[0]
    for idx, url in enumerate(urls):
        gid = int(re.findall(f"^https://{_config.website}/g/([0-9]*)/.*", url)[0])
        gal_token = re.findall(rf"^https://{_config.website}/g/[0-9]*/(\w*)/?", url)[0]
        urls[idx] = [gid, gal_token, fav_time[idx]]
    return urls

def fav_next(text: bytes):
    page = HTML(text)
    result = page.xpath("//a[@id='dnext']/@href")
    if len(result) == 0:
        return
    else:
        return result[0]
