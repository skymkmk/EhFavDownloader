import asyncio
import json
import os.path
import re
import time

from iso639 import languages
from loguru import logger

import config
import exitcodes
import sql as sql
from pageparser import *
from utils import get

if config.enable_tag_translation:
    with open(os.path.join(config.WORKING_DIR, 'translation.json'), 'r', encoding='UTF-8') as f:
        origin_trans = json.load(f)['data']
        trans = {}
        for item in origin_trans:
            trans[item['namespace']] = item['data']

SEARCH_TAG_NAMESPACE = re.compile(r"(\w+?):(.+)")


def _append_metadata(metadata_list: list, namespace: str, tag: str) -> None:
    if config.enable_tag_translation:
        try:
            metadata_list.append(trans[namespace][tag]['name'])
        except KeyError:
            logger.warning(f"Not found the translation of {namespace}:{tag}")
            metadata_list.append(tag)
    else:
        metadata_list.append(tag)


def update_metadata() -> None:
    api_request_time = 0
    for favicat in range(0, 10):
        flag = True
        page_num = 1
        url = f"https://{config.website}/favorites.php?favcat={favicat}"
        while True:
            logger.info(f'Updating category {favicat + 1}-{sql.select_category_name(favicat + 1)}, page {page_num}')
            page = asyncio.run(get(url))
            if not is_sorted_by_favorite_time(page):
                asyncio.run(get(url + "?inline_set=fs_f"))
                logger.info("Change favorite order to favorited time.")
                continue
            if not is_displayed_as_minimal(page):
                asyncio.run(get(url + '?inline_set=dm_m'))
                logger.info("Change favorite display as minimal.")
                continue
            results = parse_fav_galleries_list(page)
            if results is None:
                break
            fav_list = results[0]
            next_url = results[1]
            # Get gallery information
            for i in range(0, (len(fav_list) - 1) // 25 + 1):
                if len(fav_list) - i * 25 >= 25:
                    gidlist = [[j[0], j[1]] for j in fav_list[i * 25: i * 25 + 25]]
                else:
                    gidlist = [[j[0], j[1]] for j in fav_list[i * 25:]]
                data = {
                    'method': 'gdata',
                    'gidlist': gidlist,
                    'namespace': 1
                }
                # Use while True to deal with the api error.
                api_retry_time = 0
                while True:
                    if api_request_time < 5:
                        try:
                            api_result = json.loads(asyncio.run(get('https://api.e-hentai.org/api.php',
                                                                    data=json.dumps(data))))
                            api_request_time += 1
                            api_result = api_result['gmetadata']
                            break
                        except KeyError:
                            if api_retry_time < config.retry_time:
                                logger.warning('Failed to fetch ehapi. Sleep for 5 secs.')
                                api_retry_time += 1
                                time.sleep(5)
                            else:
                                logger.error("Error to fetch ehapi.")
                                logger.error(api_result)
                                exit(exitcodes.CANT_FETCH_EHAPI)
                    else:
                        api_request_time = 0
                        logger.info('Sleep for 5 secs to fetch ehapi.')
                        time.sleep(5)
                for j in api_result:
                    artist = []
                    group = []
                    tags = []
                    language = 'ja'
                    if 'title_jpn' in j:
                        title = j['title_jpn']
                    else:
                        title = j['title']
                    for k in j['tags']:
                        tag: str
                        namespace, tag = SEARCH_TAG_NAMESPACE.findall(k)[0]
                        if namespace == "language":
                            language = languages.get(name=tag.capitalize()).alpha2
                        elif namespace == "artist":
                            _append_metadata(artist, namespace, tag)
                        elif namespace == "group":
                            _append_metadata(group, namespace, tag)
                        else:
                            _append_metadata(tags, namespace, tag)
                    artist = ','.join(set(artist))
                    group = ','.join(set(group))
                    tags = ','.join(set(tags))
                    for k in gidlist:
                        if k[0] == int(j['gid']):
                            favorite_time = k[2]
                            break
                    sql.update_doujinshi(int(j['gid']), token=j['token'], category_id=favicat + 1, title=title,
                                         artist=artist, group=group, tag=tag, language=language,
                                         favorite_time=favorite_time)
            if next_url is not None:
                url = next_url
                page_num += 1
            else:
                break
    logger.success("Update favourites info success.")
