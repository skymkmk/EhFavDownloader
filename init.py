import asyncio
import os

import alembic.config, alembic.command
from loguru import logger

import config
import pageparser
import sql
from utils import get


def init():
    os.chdir(config.WORKING_DIR)
    # New database structure
    sql.create_database()
    alembic_config = alembic.config.Config(os.path.join(config.WORKING_DIR, 'alembic.ini'))
    alembic.command.upgrade(alembic_config, 'head')
    # Download EHTagTranslation
    if config.enable_tag_translation:
        if not os.path.exists(os.path.join(config.WORKING_DIR, 'translation.json')):
            logger.info('Downloading EhTagTranslation...')
            result = asyncio.run(get('https://raw.githubusercontent.com/EhTagTranslation/DatabaseReleases/master/'
                                     'db.text.json'))
            with open(os.path.join(config.WORKING_DIR, 'translation.json',), 'w', encoding='UTF-8') as f:
                f.write(result.decode(encoding='UTF-8'))
    # New save path if not exists
    if not os.path.exists(config.save_path):
        os.makedirs(config.save_path)
    dirs = [i for i in os.listdir(config.save_path) if os.path.isdir(os.path.join(config.save_path, i))]
    tmp = []
    # Detect unrelated pages
    for i in dirs:
        try:
            int(i.split('-')[0])
            tmp.append(i)
        except ValueError:
            logger.warning(f"Detected unrelated dir {i}.")
    dirs = tmp
    fav_page = asyncio.run(get(f"https://{config.website}/favorites.php"))
    result = pageparser.parse_fav_category_list(fav_page)
    # Iterate through all collection pages
    for idx, name in enumerate(result):
        flag = True
        # Check existed dirs and create new folder if not exist
        for i in dirs:
            if int(i.split('-')[0]) == idx:
                if i.split('-')[1] != name:
                    os.rename(os.path.join(config.save_path, i),
                              os.path.join(config.save_path, f"{idx}-{name}"))
                flag = False
                break
        if flag:
            os.mkdir(os.path.join(config.save_path, f"{idx}-{name}"))
        # Update database for category
        sql.update_category(idx, name)
    logger.success("Init dirs success.")
