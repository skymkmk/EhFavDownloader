import asyncio
import re
import sqlite3

from loguru import logger
from lxml.etree import HTML

import src.config
from src.utils import get

config = src.config.Config()
db_dir = src.config.db_dir

@logger.catch
def update_data():
    for i in range(0, 10):
        flag = True
        url = f"https://{config.website}/favorites.php?favcat={i}&inline_set=dm_e"
        page_num = 0
        while flag:
            page_num += 1
            logger.info(f'Updating category {i + 1}, page {page_num}')
            content = asyncio.run(get(url))
            page = HTML(content)
            titles = page.xpath("//form[@id='favform']/table/tr//div[@class='glink']/text()")
            urls = page.xpath("//form[@id='favform']/table/tr//div[contains(@class, 'glname')]/../@href")
            if 0 in [len(titles), len(urls)]:
                notice = page.xpath("//div[@class='ido']/p/text()")
                if len(notice) != 1:
                    logger.error(content.decode())
                    exit(1)
                else:
                    logger.info(f"Not found any favorites in category {i + 1}. Message: {notice[0]}")
            # Get gallery information
            for title, url in zip(titles, urls):
                try:
                    gid = int(re.findall(f"^https://{config.website}/g/([0-9]*)/.*", url)[0])
                    gal_token = re.findall(rf"^https://{config.website}/g/[0-9]*/(\w*)/?", url)[0]
                    with sqlite3.connect(db_dir) as conn:
                        result = conn.execute("SELECT * FROM doujinshi WHERE gid = ?", (gid,)).fetchall()
                        if len(result) == 0:
                            conn.execute("INSERT INTO doujinshi (gid, title, token, category_id)"
                                         "VALUES (?, ?, ?, ?)", (gid, title, gal_token, i + 1,))
                            conn.commit()
                        else:
                            conn.execute("UPDATE doujinshi SET title = ?, token = ? WHERE gid = ?",
                                         (title, gal_token, gid,))
                            conn.commit()
                except ValueError:
                    logger.warning("Gid is not a integer anymore. Contact skymkmk(admin@skymkmk.com) for more"
                                   "information.")
                    logger.warning(f"Error url: {url}")
            next_page = page.xpath("//a[@id='dnext']")
            if len(next_page) == 0:
                flag = False
            else:
                url = next_page[0].xpath('./@href')[0] + '&inline_set=dm_e'
    logger.success("Update favourites info success.")
