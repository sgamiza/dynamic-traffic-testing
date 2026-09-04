# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""
import datetime
import time
import os
import logging
import threading
import queue
from .optional_lab import AdminApiConnectionClosedException, admin


WHITELIST = ["61524", "4654", "61652", "4655", "61649"]

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

class BBUAlarmManager:
    def __init__(self, ip, whitelist=WHITELIST):
        self.ip = ip
        self.whitelist = whitelist
        self.bbu_api = admin()
        self.is_connected = False
        self.setup_logging()


    def setup_logging(self):
        log_directory = "bbulog"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file_path = os.path.join(log_directory, 'alarms.log')

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        file_handler.setFormatter(file_formatter)

        # 创建流处理器
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        stream_handler.setFormatter(stream_formatter)

        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        # logger.addHandler(stream_handler)


    def connect(self):
        if not self.is_connected:
            try:
                self.bbu_api.connect_to(bts_host=self.ip)
                self.is_connected = True
                logging.info(f"成功连接到 {self.ip}")
            except AdminApiConnectionClosedException:
                # logging.warning("连接失败。5分钟后重试。")
                time.sleep(60 * 5)
                self.bbu_api.connect_to(bts_host=self.ip)
                self.is_connected = True
                logging.info(f"成功连接到 {self.ip}")
        return self



    def get_active_alarms(self):
        id = self.get_active_alarms_list()
        end_time = time.time()
        dt_object = datetime.datetime.fromtimestamp(end_time)
        logging.info(f"{dt_object.strftime('%Y-%m-%d_%H-%M-%S')} get_active_alarms")
        return '\n'.join([str(item) for item in id])

    def get_active_alarms_list(self):
        return self.bbu_api.get_active_alarms()

    def process_alarms(self):
        try:
            active_alarms = self.get_active_alarms_list()
            logging.info(f"checking alarm ...")
            for alarm in active_alarms:
                fault_id = str(alarm['faultId'])
                logging.info(f"there is alarm id: {fault_id}")
                # print(fault_id, alarm['alarmDetail'])
                if fault_id not in self.whitelist:
                    # print(f"process_alarms：found faultId: {fault_id}")
                    logging.error(f"found faultId: {fault_id}")
                    # TODO 主进程如何去捕获
                    # 一个错误直接raise，非全部
                    raise ValueError(f"found faultId: {fault_id}")
        except Exception as e:
            logging.error(f"error: {e}")
            # self.bbu_api.teardown()
            raise
        # finally:
        #     self.bbu_api.teardown()


    def disconnect(self):
        if self.is_connected:
            self.bbu_api.teardown()
            self.is_connected = False
            # logging.info(f"已断开与 {self.ip} 的连接")


    def run(self):
        """
        run bbu alarm check
        :return:
        """
        if not self.is_connected:
            # logging.error("未连接到BBU API，请先调用connect方法。")
            return

        start_time = time.time()
        self.process_alarms()
        end_time = time.time()
        logging.info(f"run: {end_time - start_time}s")


class AlarmThread(threading.Thread):
    def __init__(self, ip, terminate_flag, exception_queue):
        super().__init__()
        self.ip = ip
        self.terminate_flag = terminate_flag
        self.exception_queue = exception_queue
        self.exception = None

    def run(self):
        alarm_manager = BBUAlarmManager(self.ip)
        while not self.terminate_flag.is_set():
            try:
                # time.sleep(60)
                alarm_manager.connect().run()
            except ValueError as e:
                self.exception = e
                self.exception_queue.put(e)

                # TODO 发现告警是否需要退出
                # break
            time.sleep(60*10)
        alarm_manager.disconnect()


def check_alarm(ip, terminate_flag, exception_queue):
    alarm_manager = BBUAlarmManager(ip)
    while not terminate_flag.is_set():
        try:
            alarm_manager.connect().run()
        except ValueError as e:
            exception_queue.put(e)
            break
        time.sleep(60)
    alarm_manager.disconnect()



# if __name__ == '__main__':
    # 普通调用
    # IP = '127.0.0.1'  # TEST_DUT stability
    # alarm_manager = BBUAlarmManager(IP)
    # alarm_manager.connect().run()

    # 线程调用
    # IP = '127.0.0.1'
    # terminate_flag = threading.Event()
    #
    # check_thread = AlarmThread(IP, terminate_flag,queue.Queue())
    # check_thread.start()
    #
    # # 没有告警无法退出
    # while check_thread.is_alive():
    #     if check_thread.exception:
    #         print(f"__main__：发现未授权的faultId")
    #         raise check_thread.exception
    #
    # terminate_flag.set()
    # check_thread.join()

