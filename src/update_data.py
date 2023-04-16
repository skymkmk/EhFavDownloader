import asyncio
import json
import os.path
import re
import sqlite3
import time

import src.sql as sql

from loguru import logger
from lxml.etree import HTML

import src.pageParser as pageParser
import src.config
from src.utils import get

config = src.config.Config()


def update_data() -> None:
    if config.enable_artist_translation:
        with open(os.path.join(config.working_dir, 'translation.json'), 'r', encoding='UTF-8') as f:
            trans = json.load(f)['data']
            for i in trans:
                if i['namespace'] == 'artist':
                    trans = i['data']
                    break
    api_request_time = 0
    for favicat in range(0, 10):
        flag = True
        page_num = 1
        url = f"https://{config.website}/favorites.php?favcat={favicat}&inline_set=dm_m"
        while flag:
            logger.info(f'Updating category {favicat + 1}-{sql.select_category_name(favicat + 1)}, page {page_num}')
            content = asyncio.run(get(url))
            with open('a.html', 'w', encoding='UTF-8') as f:
                f.write(content.decode())
            results = pageParser.fav_page(content)
            if type(results) is str:
                logger.info(results)
                return
            results = [{'gid': i[0], 'token': i[1], 'fav_time': i[2]} for i in results]
            # Get gallery information
            for i in range(0, (len(results) - 1) // 25 + 1):
                if len(results) - i * 25 >= 25:
                    gidlist = [[i['gid'], i['token']] for i in results[i * 25: i * 25 + 25]]
                else:
                    gidlist = [[i['gid'], i['token']] for i in results[i * 25: -1]]
                data = {
                    'method': 'gdata',
                    'gidlist': gidlist,
                    'namespace': 1
                }
                while True:
                    if api_request_time < 5:
                        try:
                            result = json.loads(asyncio.run(get('https://api.e-hentai.org/api.php',
                                                                data=json.dumps(data))))
                            result = result['gmetadata']
                        except KeyError:
                            logger.error('Failed to fetch ehapi.')
                            logger.exception(result)
                        api_request_time += 1
                        break
                    else:
                        api_request_time = 0
                        logger.info('Sleep for 5 secs to fetch ehapi.')
                        time.sleep(5)
                for i in result:
                    artist = ''
                    for j in i['tags']:
                        if 'artist:' in j:
                            if config.enable_artist_translation:
                                if j.replace('artist:', '', 1) in trans:
                                    artist += trans[j.replace('artist:', '', 1)]['name']
                                else:
                                    artist += j.replace('artist:', '', 1)
                            else:
                                artist += j.replace('artist:', '', 1)
                            artist += ' '
                    for j in results:
                        if i['gid'] in j.values():
                            favorite_time = j['fav_time']
                            break
                    sql.update_doujinshi(i['gid'], i['token'], favicat + 1, i['title_jpn'] if 'title_jpn' in i and
                                                                                              i['title_jpn'] != ''
                    else i['title'], artist=artist if artist != '' else None, favorited_time=favorite_time, kwargs=i)
            next_page = pageParser.fav_next(content)
            if next_page is not None:
                url = next_page + '&inline_set=dm_m'
                page_num += 1
            else:
                flag = False
    logger.success("Update favourites info success.")
