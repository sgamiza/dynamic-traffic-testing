# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""

import os
import sqlite3
import datetime
import logging
import pandas as pd
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class DeviceDB:
    def __init__(self, path: Optional[str] = None) -> None:
        if not path:
            path = self._create_db_path()
        self._path = path
        self._conn = None
        self._cursor = None
        self.connect()
        self.create_table()

    def _create_db_path(self, base_path="db", file_prefix="result", extension=".db"):
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        test_date = datetime.datetime.now().strftime('_%m%d%Y_%I%M%S')
        path = os.path.join(base_path, f"{file_prefix}{test_date}{extension}")
        return path

    def connect(self) -> bool:
        try:
            self._conn = sqlite3.connect(self._path)
            logger.debug(f'Init sqlite connection with version: {sqlite3.version}')
        except Exception as err:
            logger.debug(f'Connect error: {err}')
            return False
        else:
            self._cursor = self._conn.cursor()
            return True

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

    def create_table(self) -> None:
        """
        ('26997', '127.0.0.1', 'profile_100', 69)
        :return:
        """
        try:
            self._cursor.execute('''
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    ip TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    bandwidth TEXT NOT NULL,
                    power FLOAT NOT NULL,
                    comment TEXT,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Create table error: {err}')

        self._create_trigger()

    def _create_trigger(self) -> None:
        try:
            self._cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS insert_timestamp
                AFTER INSERT ON data
                FOR EACH ROW
                BEGIN
                    UPDATE data
                    SET timestamp = datetime('now', 'localtime')
                    WHERE id = NEW.id;
                END;
            ''')
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Create trigger error: {err}')


    def insert_data1(self, pid: str, ip: str, profile: str, bandwidth: str, power: float, ) -> None:
        # print(pid, ip, profile, bandwidth, power)
        try:
            self._cursor.execute('''
                INSERT INTO data ( pid, ip,profile, bandwidth, power)
                VALUES (?, ?, ?, ?, ?)
            ''', (pid, ip, profile, bandwidth, power))
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Insert data error: {err}')

    def insert_data(self, pid: str, ip: str, profile: str, bandwidth: str, power: float, comment: str = None) -> None:
        try:
            if comment is not None:
                sql = '''
                    INSERT INTO data (pid, ip, profile, bandwidth, power, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                params = (pid, ip, profile, bandwidth, power, comment)
            else:
                sql = '''
                    INSERT INTO data (pid, ip, profile, bandwidth, power)
                    VALUES (?, ?, ?, ?, ?)
                '''
                params = (pid, ip, profile, bandwidth, power)

            self._cursor.execute(sql, params)
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Insert data error: {err}')

    def query_data(self) -> List[Tuple[int, str, str, float, int, str]]:
        try:
            self._cursor.execute('SELECT * FROM data')
            rows = self._cursor.fetchall()
            return rows
        except Exception as err:
            logger.debug(f'Query data error: {err}')
            return []

    def update_data(self, profile: str, new_bandwidth: str) -> None:
        try:
            self._cursor.execute('''
                UPDATE data
                SET bandwidth = ?
                WHERE profile = ?
            ''', (new_bandwidth, profile))
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Update data error: {err}')

    def delete_data(self, profile: str) -> None:
        try:
            self._cursor.execute('''
                DELETE FROM data
                WHERE profile = ?
            ''', (profile,))
            self._conn.commit()
        except Exception as err:
            logger.debug(f'Delete data error: {err}')

    # utill may need
    def query_and_insert(self, ip: str, pipe: int, case: str, idn: str) -> Optional[str]:
        try:
            sql_query = f'SELECT * FROM deviceTable WHERE IP = "{ip}"'
            self._cursor.execute(sql_query)
            ret = self._cursor.fetchone()
            if ret is None:
                sql_insert = f'INSERT INTO deviceTable VALUES("{ip}", {pipe}, "{case}", "{idn}")'
                self._cursor.execute(sql_insert)
                self._conn.commit()
            else:
                _, pipe_index, case_name, idn_str = ret
                if pipe_index != pipe:
                    return f'{ip} was used for Pipe{pipe_index} case: {case} with IDN: {idn}'
        except Exception as err:
            logger.debug(f'Query and insert error: {err}')
            return f'Pipe{pipe} device IP checking failed with err: {err}'


# if __name__ == '__main__':
#     try:
#         db = DeviceDB()
#         # db.connect()
#         # db.create_table()
#         db.insert_data('9616', '127.0.0.1', "profile_100", "69", -13.083730)
#         db.insert_data('9616', '127.0.0.1', "profile_100", "69", -13.083730)
#         db.insert_data('9616', '127.0.0.1', "profile_99", "69", -13.083730)
#         db.insert_data('9616', '127.0.0.1', "profile_98", "69", -13.083730)
#         print(db.query_data())
#         print()
#         db.update_data('profile_99', '30')
#         print(db.query_data())
#         print()
#         # db.delete_data('Profile2')
#         # print(db.query_data())
#         # db.save_db_to_excel("_05_result.xlsx")
#
#         db.close()
#
#     except Exception as err:
#         print(err)
#         raise
