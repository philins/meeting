import os
from typing import Dict, List, Tuple

import sqlite3


conn = sqlite3.connect(os.path.join("db", "meeting.db"))
cursor = conn.cursor()

DB = os.path.join("db", "meeting.db")


def del_me(user_id) -> int:
    """
    Удаляет пользователя
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            DELETE FROM users 
            WHERE id={user_id}""")
        conn.commit()
        cursor.execute(
            f"""
            UPDATE users 
            SET companion_id=null 
            WHERE companion_id={user_id};""")
        conn.commit()


def get_companion(user_id) -> int:
    """
    Получает id собеседника
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            WHERE companion_id=?
            LIMIT 1;""", (user_id,))
        return cursor.fetchone()


def find_companion(user_id):
    """
    Выбирает случайного собеседника из базы
    """
    user = get_user_data(user_id)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            WHERE id!=? AND gender != ?
            AND companion_id is null
            ORDER BY RANDOM()
            LIMIT 1;""", (user_id, user[3]))
        companion = cursor.fetchone()
        if companion:
            return companion
        cursor.execute("""
            SELECT * FROM users
            WHERE id!=?
            AND companion_id is null
            ORDER BY RANDOM()
            LIMIT 1;""", (user_id,))
        companion = cursor.fetchone()
        return companion


def set_companion(user_id, companion_id):
    """
    Записывает собеседника
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE users 
            SET companion_id={companion_id} 
            WHERE id={user_id};""")
        conn.commit()


def drop_companion(user_id):
    """
    Сбрасывает собеседника
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE users 
            SET companion_id=null 
            WHERE id={user_id};""")
        conn.commit()


def get_user_data(user_id):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            WHERE id=?
            LIMIT 1;""", (user_id,))
        return cursor.fetchone()


def get_total_users():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        out = {}
        cursor.execute("SELECT count(*) FROM users;")
        out['total'] = cursor.fetchone()[0]
        for col in ['gender','age','lang']:
            cursor.execute(f"SELECT {col}, count({col}) FROM users GROUP BY {col} ORDER BY {col};")
            for line in cursor.fetchall():
                out[line[0]] = line[1]
        return out


def insert(table: str, column_values: Dict):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        columns = ', '.join( column_values.keys() )
        values = [tuple(column_values.values())]
        placeholders = ", ".join( "?" * len(column_values.keys()) )
        cursor.executemany(
            f"INSERT OR REPLACE INTO {table} "
            f"({columns}) "
            f"VALUES ({placeholders})",
            values)
        conn.commit()


def fetchall(table: str, columns: List[str]) -> List[Tuple]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def delete(table: str, row_id: int) -> None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        row_id = int(row_id)
        cursor.execute(f"delete from {table} where id={row_id}")
        conn.commit()


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='users'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()

check_db_exists()
