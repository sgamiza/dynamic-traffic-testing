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
from .database import DeviceDB

logger = logging.getLogger(__name__)


class Result:
    def __init__(self, db: DeviceDB) -> None:
        self.db = db

    def query_power_above_threshold(self, threshold: float = 40.0) -> List[Tuple[int, str, str, str, float, str, str]]:
        try:
            self.db._cursor.execute('SELECT * FROM data WHERE power > ?', (threshold+3,))
            rows = self.db._cursor.fetchall()
            return rows

        except Exception as err:
            logger.debug(f'Query power above threshold error: {err}')
            return []


    def save_db_to_excel(self, excel_path: str, p_max_config: float) -> List[Tuple[int, str, str, str, float, str, str]]:
        directory = os.path.dirname(excel_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            rows = self.query_power_above_threshold(p_max_config)

            # 方式2
            # rows = self.db.query_power_above_threshold()
            # df = pd.DataFrame(rows, columns=['id', 'pid', 'ip', 'profile', 'bandwidth', 'power', 'comment', 'timestamp'])
            # df.to_excel(excel_path, index=False)

            # 方式1
            query = "SELECT * FROM data"
            df = pd.read_sql_query(query, self.db._conn)
            df.to_excel(excel_path, index=False)
            logger.info(f"Database saved to Excel file: {excel_path}")
            return rows
        except Exception as err:
            logger.debug(f'Query data error: {err}')
            raise


# if __name__ == '__main__':
#     pass
    # try:
    #     db = DeviceDB()
    #     db.insert_data('9616', '127.0.0.1', "profile_100", "69", -13.083730)
    #     db.insert_data('9616', '127.0.0.1', "profile_100", "69", -21.083730)
    #     db.insert_data('9616', '127.0.0.1', "profile_99", "69", -19.083730)
    #     db.insert_data('9616', '127.0.0.1', "profile_98", "69", -25.083730)
    #     print(db.query_data())
    #     print()
    #     db.update_data('profile_99', '30')
    #     print(db.query_data())
    #     print()
    #
    #     result = Result(db)
    #     rows_above_threshold = result.save_db_to_excel("result/result2.xlsx")
    #     print(rows_above_threshold)
    #
    #     db.close()
    #
    # except Exception as err:
    #     print(err)
    #     raise
