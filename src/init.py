import asyncio
import os
import sqlite3

import alembic.config, alembic.command
from loguru import logger
from lxml.etree import HTML

from src import pageParser
from src import sql
from src.utils import get
from .config import Config
from .config import db_dir

config = Config()
working_dir = os.path.split(os.path.split(__file__)[0])[0]


@logger.catch
def init():
    # New database structure
    with sqlite3.connect(db_dir) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS category (id integer NOT NULL PRIMARY KEY AUTOINCREMENT,"
                     "name text NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS doujinshi (gid integer NOT NULL PRIMARY KEY, title text NOT NULL,"
                     "page_num integer NOT NULL DEFAULT 0, token text NOT NULL, category_id integer NOT NULL,"
                     "status integer NOT NULL DEFAULT 0, artist text, parent_gid integer, parent_key text,"
                     "first_gid integer, first_key text, current_gid integer, current_key text, favorited_time date,"
                     "CONSTRAINT fk_catgory FOREIGN KEY (category_id) REFERENCES category(id))")
        conn.execute("CREATE TABLE IF NOT EXISTS img (id text NOT NULL, page_num integer NOT NULL,"
                     "gid integer NOT NULL, finished integer NOT NULL DEFAULT 0, md5 text,"
                     "PRIMARY KEY (id, page_num, gid),"
                     "CONSTRAINT fk_gid FOREIGN KEY (gid) REFERENCES doujinshi(gid))")
        conn.commit()
    alembic_config = alembic.config.Config(os.path.join(working_dir, 'alembic.ini'))
    alembic.command.upgrade(alembic_config, 'head')
    # Download EHTagTranslation
    if config.enable_artist_translation:
        if not os.path.exists(os.path.join(working_dir, 'translation.json')):
            logger.info('Downloading EhTagTranslation...')
            result = asyncio.run(get('https://raw.githubusercontent.com/EhTagTranslation/DatabaseReleases/master/db.text.json'))
            with open(os.path.join(working_dir, 'translation.json',), 'w', encoding='UTF-8') as f:
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
    result = pageParser.fav_category(fav_page)
    # Iterate through all collection pages
    for idx, name in result:
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
