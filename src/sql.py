import os
import sqlite3

_working_dir = os.path.split(os.path.split(__file__)[0])[0]
_db_dir = os.path.join(_working_dir, 'data.db')


def update_category(cid: int, name: str) -> None:
    # Update database for category
    with sqlite3.connect(_db_dir) as conn:
        result = conn.execute("SELECT * FROM category WHERE id = ?", (cid,)).fetchall()
        if len(result) == 0:
            conn.execute("INSERT INTO category (name) VALUES(?)", (name,))
            conn.commit()
        elif result[0][1] != name:
            conn.execute("UPDATE category SET name = ? WHERE id = ?", (name, cid))
            conn.commit()


def select_category_name(cid: int) -> str:
    with sqlite3.connect(_db_dir) as conn:
        result = conn.execute("SELECT name FROM category WHERE id = ?", (cid,)).fetchall()[0][0]
    return result


def update_doujinshi(gid: int, token: str, cid: int, title: str, **kwargs) -> None:
    arguments = ['artist', 'parent_gid', 'parent_key', 'first_gid', 'first_key', 'current_gid', 'current_key',
                 'favorited_time']
    with sqlite3.connect(_db_dir) as conn:
        result = conn.execute("SELECT * FROM doujinshi WHERE gid = ?", (gid,)).fetchall()
        columns = ['gid', 'token', 'category_id', 'title']
        columns.extend([i for i in kwargs.keys() if i in arguments])
        values = [gid, token, cid, title]
        values.extend([i[1] for i in kwargs.items() if i[0] in arguments])
        if len(result) == 0:
            values = tuple(values)
            placeholders = ', '.join('?' * len(columns))
            conn.execute(f"INSERT INTO doujinshi ({', '.join(columns)})"
                         f"VALUES ({placeholders})", values)
            conn.commit()
        else:
            columns.pop(0)
            values.append(values[0])
            values.pop(0)
            values = tuple(values)
            conn.execute(f"UPDATE doujinshi SET {' = ?, '.join(columns) + ' = ?'} WHERE gid = ?",
                         values)
            conn.commit()
