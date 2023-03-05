import asyncio
import os
import sqlite3

from loguru import logger
from lxml.etree import HTML

import src.config
from src.utils import get


@logger.catch
def init(config: dict):
    db_dir = src.config.db_dir
    # New database structure
    with sqlite3.connect(db_dir) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS category (id integer NOT NULL PRIMARY KEY AUTOINCREMENT,"
                     "name text NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS doujinshi (gid integer NOT NULL PRIMARY KEY, title text NOT NULL,"
                     "page_num integer NOT NULL DEFAULT 0, token text NOT NULL, category_id integer NOT NULL,"
                     "finished integer NOT NULL DEFAULT 0,"
                     "CONSTRAINT fk_catgory FOREIGN KEY (category_id) REFERENCES category(id))")
        conn.execute("CREATE TABLE IF NOT EXISTS img (id text NOT NULL, page_num integer NOT NULL,"
                     "gid integer NOT NULL, finished integer NOT NULL DEFAULT 0, PRIMARY KEY (id, page_num, gid),"
                     "CONSTRAINT fk_gid FOREIGN KEY (gid) REFERENCES doujinshi(gid))")
        conn.commit()
    # New save path if not exists
    if not os.path.exists(config['save_path']):
        os.makedirs(config['save_path'])
    dirs = [i for i in os.listdir(config['save_path']) if os.path.isdir(os.path.join(config['save_path'], i))]
    tmp = []
    # Detect unrelated pages
    for i in dirs:
        try:
            int(i.split('-')[0])
            tmp.append(i)
        except ValueError:
            logger.warning(f"Detected unrelated dir {i}.")
    dirs = tmp
    fav_page = asyncio.run(get(f"https://{config['website']}/favorites.php", config))
    fav_tree = HTML(fav_page)
    # Check if the fav page meets the requirements
    if len(fav_tree.xpath("//div[@class='nosel']/div[@class='fp']")) == 0:
        logger.error(fav_page.decode())
        exit(1)
    # Iterate through all collection pages
    for idx, node in enumerate(fav_tree.xpath("//div[@class='nosel']/div[@class='fp']")):
        name = node.xpath('./div[3]/text()')[0]
        flag = True
        # Check existed dirs and create new folder if not exist
        for i in dirs:
            if int(i.split('-')[0]) == idx + 1:
                if i.split('-')[1] != name:
                    os.rename(os.path.join(config['save_path'], i),
                              os.path.join(config['save_path'], f"{idx + 1}-{name}"))
                flag = False
                break
        if flag:
            os.mkdir(os.path.join(config['save_path'], f"{idx + 1}-{name}"))
        # Update database for category
        with sqlite3.connect(db_dir) as conn:
            result = conn.execute("SELECT * FROM category WHERE id = ?", (idx + 1,)).fetchall()
            if len(result) == 0:
                conn.execute("INSERT INTO category (name) VALUES(?)", (name,))
                conn.commit()
            elif result[0][1] != name:
                conn.execute("UPDATE category SET name = ? WHERE id = ?", (name, idx + 1))
                conn.commit()
    logger.success("Init dirs success.")
