import atexit
import sqlite3
from typing import Union, List, Tuple

import config

conn = sqlite3.connect(config.DB_DIR)
atexit.register(conn.close)


def create_database() -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS category (id integer NOT NULL PRIMARY KEY AUTOINCREMENT,"
                 "name text NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS doujinshi (gid integer NOT NULL PRIMARY KEY, token text NOT NULL,"
                 "category_id integer NOT NULL, page_num integer NOT NULL DEFAULT 0, status integer NOT NULL DEFAULT 0,"
                 "title text NOT NULL, artist text, publisher text, tag text, language text, favorited_time text,"
                 "CONSTRAINT fk_catgory FOREIGN KEY (category_id) REFERENCES category(id))")
    conn.execute("CREATE TABLE IF NOT EXISTS img (id text NOT NULL, page_num integer NOT NULL,"
                 "gid integer NOT NULL, finished integer NOT NULL DEFAULT 0, md5 text,"
                 "PRIMARY KEY (id, page_num, gid),"
                 "CONSTRAINT fk_gid FOREIGN KEY (gid) REFERENCES doujinshi(gid))")
    conn.commit()


def update_category(cid: int, name: str) -> None:
    # Update database for category
    result = conn.execute("SELECT * FROM category WHERE id = ?", (cid,)).fetchall()
    if len(result) == 0:
        conn.execute("INSERT INTO category (name) VALUES(?)", (name,))
        conn.commit()
    elif result[0][1] != name:
        conn.execute("UPDATE category SET name = ? WHERE id = ?", (name, cid))
        conn.commit()


def select_category_name(cid: int) -> Union[str, None]:
    result = conn.execute("SELECT name FROM category WHERE id = ?", (cid,)).fetchall()
    if len(result) == 0:
        return
    return result[0][0]


def select_doujinshi_for_download() -> List[Tuple[int, str, int, str, int]]:
    result = conn.execute("SELECT gid, token, page_num, title, category_id FROM doujinshi WHERE status = 0").fetchall()
    return result


def update_doujinshi(gid: int, **kwargs) -> None:
    arguments = ['token', 'category_id', 'page_num', 'title', 'artist', 'publisher', 'tag', 'language',
                 'favorited_time']
    result = conn.execute("SELECT * FROM doujinshi WHERE gid = ?", (gid,)).fetchall()
    columns = ['gid']
    columns.extend([i for i in kwargs.keys() if i in arguments])
    values = [gid]
    values.extend([i[1] for i in kwargs.items() if i[0] in arguments])
    if len(result) == 0:
        values = tuple(values)
        placeholders = ', '.join('?' * len(columns))
        conn.execute(f"INSERT INTO doujinshi ({', '.join(columns)}) VALUES ({placeholders})", values)
        conn.commit()
    else:
        columns.pop(0)
        values.append(values[0])
        values.pop(0)
        values = tuple(values)
        conn.execute(f"UPDATE doujinshi SET {' = ?, '.join(columns) + ' = ?'} WHERE gid = ?",
                     values)
        conn.commit()


def update_gallery_success(gid: int) -> None:
    conn.execute("UPDATE doujinshi SET status = 1 WHERE gid = ?", (gid,))
    conn.commit()


def update_doujinshi_as_dmca(gid: int) -> None:
    conn.execute("UPDATE doujinshi SET status = 2 WHERE gid = ?", (gid,))
    conn.commit()


def select_img_info(gid: int) -> List[Tuple[int, str]]:
    result = conn.execute("SELECT page_num, id FROM img WHERE gid = ? and finished = 0", (gid,)).fetchall()
    return result


def select_img_counts(gid: int) -> int:
    return conn.execute("SELECT count(id) FROM img WHERE gid = ?", (gid,)).fetchall()[0][0]


def update_img_info(ptoken: str, page_num: int, gid: int) -> None:
    result = conn.execute("SELECT * FROM img WHERE id = ? and page_num = ? and gid = ?",
                          (ptoken, page_num, gid)).fetchall()
    if len(result) == 0:
        conn.execute("INSERT INTO img (id, page_num, gid) VALUES (?, ?, ?)", (ptoken, page_num, gid))
        conn.commit()
    else:
        conn.execute("UPDATE img SET id = ? WHERE page_num = ? and gid = ?", (ptoken, page_num, gid))
        conn.commit()


def update_img_success(gid: int, ptoken: str, md5: str) -> None:
    conn.execute("UPDATE img SET finished = 1, md5 = ? WHERE id = ? and gid = ?", (md5, ptoken, gid))
    conn.commit()
