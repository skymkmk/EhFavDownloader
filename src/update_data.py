import asyncio
import os
import re
import sqlite3

from loguru import logger
from lxml.etree import HTML

from src.utils import get


# Since e-hentai updates the gallery links in the favorites, the following code is useless
# @logger.catch
# def _check_gallery_update(check_list: list, config: dict, retry_time=5):
#     if retry_time > 0:
#         resp = json.loads(asyncio.run(get("https://api.e-hentai.org/api.php", config, json.dumps({
#             "method": "gdata",
#             "gidlist": check_list,
#             "namespace": 1
#         }))))
#         if 'gmetadata' in resp:
#             for i in resp['gmetadata']:
#                 if "current_gid" in i:
#                     with sqlite3.connect(os.path.join(os.getcwd(), 'data.db')) as conn:
#                         new_gallery_result = conn.execute("SELECT * FROM doujinshi WHERE gid = ?",
#                                                           (i['current_gid'],)).fetchall()
#                         if len(new_gallery_result) == 0:
#                             category = conn.execute("SELECT category_id FROM doujinshi WHERE gid = ?",
#                                                     (i['gid'],)).fetchall()
#                             category = category[0][0]
#                             title = i['title_jpn'] if i['title_jpn'] != '' else i['title']
#                             conn.execute("INSERT INTO doujinshi VALUES (?, ?, ?, ?, ?, ?)",
#                                          (i['current_gid'], title, 0, i['current_key'], category, 0,))
#                             logger.info(f"Gallery {i['gid']}-{title} has been updated."
#                                         f"The new gid is {i['current_gid']}")
#         else:
#             logger.warning(f"Failed to fetch api information. Will retry in 60 secs. Remaining retry counts:"
#                            f"{retry_time}")
#             time.sleep(60)
#             _check_gallery_update(check_list, config, retry_time - 1)
#     else:
#         logger.error("Failed to fetch api information. Will skip for gallery updating.")
#         raise FailedFetchAPI


@logger.catch
def update_data(config: dict):
    working_dir = os.path.split(os.path.realpath(__file__))[0]
    db_dir = os.path.join(working_dir, 'data.db')
    for i in range(0, 10):
        flag = True
        url = f"https://{config['website']}/favorites.php?favcat={i}"
        page_num = 0
        while flag:
            page_num += 1
            logger.info(f'Updating category {i + 1}, page {page_num}')
            content = asyncio.run(get(url, config))
            page = HTML(content)
            items = page.xpath("//form[@id='favform']//tr")
            if len(items) == 0:
                logger.error(content)
                exit(1)
            # Get gallery information
            for idx, value in enumerate(items):
                if idx != 0:
                    title = value.xpath("./td[4]//div[@class='glink']/text()")[0]
                    gal_url = value.xpath("./td[4]/a/@href")[0]
                    try:
                        gid = int(re.findall(f"^https://{config['website']}/g/([0-9]*)/.*", gal_url)[0])
                        gal_token = re.findall(f"^https://{config['website']}/g/[0-9]*/(\\w*)/?", gal_url)[0]
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
                        logger.warning(f"Error url: {gal_url}")
            next_page = page.xpath("//a[@id='dnext']")
            if len(next_page) == 0:
                flag = False
            else:
                url = next_page[0].xpath('./@href')[0]
    logger.success("Update favourites info success.")
    # Since e-hentai updates the gallery links in the favorites, the following code is useless
    # with sqlite3.connect(os.path.join(os.getcwd(), 'data.db')) as conn:
    #     result = conn.execute("SELECT gid, token FROM doujinshi").fetchall()
    # # Check if the gallery has newer version
    # result_len = len(result)
    # current_progress = 0
    # try:
    #     while len(result) != 0:
    #         if len(result) >= 25:
    #             current_progress += 25
    #             request = result[0:25]
    #             del result[0:25]
    #         else:
    #             current_progress += len(result)
    #             request = result[:]
    #             result.clear()
    #         logger.info(f"Checking gallery update. {round(current_progress / result_len * 100, 2)}%")
    #         request = [list(i) for i in request]
    #         _check_gallery_update(request, config)
    # except FailedFetchAPI:
    #     pass
