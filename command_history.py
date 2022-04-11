import sqlite3 as sq
import time
from typing import Dict
from collections.abc import Iterator


def add_hotel_info(my_dict: Dict) -> None:
    my_dict['data'] = time.asctime()
    with sq.connect('history_hotel.db') as con:
        cur = con.cursor()
        cur.execute("INSERT INTO hotels VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [my_dict['user_id'], my_dict['data'], my_dict['hotel_id'], my_dict['name'], my_dict['star_rating'],
                     my_dict['address'], my_dict['guest_reviews'], my_dict['price'], my_dict['distance'],
                     my_dict['exists_photo'], my_dict['name_command'], my_dict['checkIn'], my_dict['checkOut']])


def read_hotels_info(user_id: int) -> Iterator[Dict]:
    with sq.connect('history_hotel.db') as con:
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"SELECT * FROM hotels WHERE user_id = {user_id}")
        for result in cur:
            yield result


def init_hotels() -> None:
    with sq.connect('history_hotel.db') as con:
        cur = con.cursor()

        cur.execute('''CREATE TABLE IF NOT EXISTS hotels (
                user_id INTEGER,
                data TEXT,
                hotel_id INTEGER, 
                name TEXT,
                star_rating FLOAT,
                address TEXT,
                guest_reviews FLOAT,
                price TEXT,
                distance FLOAT,
                exists_photo INTEGER DEFAULT 1,
                name_command INTEGER,
                checkIn TEXT,
                checkOut TEXT
                )''')

        cur.execute('''CREATE TABLE IF NOT EXISTS photos (
                hotel_id INTEGER,
                name_file TEXT
                )''')


def add_photo(name_photo: str, id: int) -> None:
    with sq.connect('history_hotel.db') as con:
        cur = con.cursor()
        cur.execute("INSERT INTO photos VALUES ( ?, ?)", (id, name_photo))


def read_photo(id: int) -> Iterator[Dict]:
    with sq.connect('history_hotel.db') as con:
        con.row_factory = sq.Row
        cur = con.cursor()
        cur.execute(f"SELECT name_file FROM photos WHERE hotel_id = {id}")
        for result in cur:
            yield result['name_file']

