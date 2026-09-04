# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""
import os
import multiprocessing
import time
import datetime
import sys
import numpy as np
import signal
import yaml
import logging
import contextlib
from abc import ABC, abstractmethod
from .iperftraffic import run_iper_trafic

from .powersensor import run_powersensor
from .uecallapi import UETest
from .database import DeviceDB
from .result import Result
from .uelockcellapi import IperfManager

# Configure logging
# logger = logging.getLogger('pyvisa')
# logger.setLevel(logging.ERROR)
# logger = logging.getLogger('paramiko.transport')
# logger.setLevel(logging.ERROR)

# setup logging
# iperf_logpath = os.path.join(os.getcwd(), 'logs')
# if not os.path.isdir(iperf_logpath):
#     os.makedirs(iperf_logpath)
# test_date = str(datetime.datetime.now().strftime('_%m%d%Y_%I%M%S'))
# gLogName = os.path.basename(sys.argv[0]) + test_date + '.log'
# gLogName = os.path.join(iperf_logpath, gLogName)
#
# logging.basicConfig(filename=gLogName, format='%(levelname)s | %(asctime)s | %(message)s',
#                     datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
# logFormatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
#
logger = logging.getLogger(__name__)


# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# logger.addHandler(consoleHandler)

INSTRUMENT_PROFILE_TIMEOUT = 300

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as exc:
            print(f"Error loading YAML file: {exc}")
            return None


def generate_iperf_traffic(queue, **kwargs):
    """
    Process for iperf
    :param queue:
    :param kwargs:
    :return:
    """
    try:
        run_iper_trafic(queue, **kwargs)
    except Exception as e:
        queue.put(e)
        raise


def read_instrument(queue, ps_ip, ps_parameters, terminate_flag):
    """
    Process for instrument
    :param queue:
    :param ps_ip:
    :param terminate_flag:
    :return:
    """

    def handle_sigint(signum, frame):
        print("Caught SIGINT, performing cleanup...")
        logger.info(f"Caught SIGINT, performing cleanup... (signum: {signum}, frame: {frame})")
        logger.info(f"Frame details: File {frame.f_code.co_filename}, Line {frame.f_lineno}, Function {frame.f_code.co_name}")
        exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        while not terminate_flag.is_set():
            data = run_powersensor(ip=ps_ip, profile=ps_parameters)
            # print("debug power sensor: ",data)
            queue.put(data)
            # todo 1秒4次
            # time.sleep(5)  # 读取一次数据
    except Exception as err:
        raise
    finally:
        print("Performing cleanup...")


# @contextlib.contextmanager
# def run_iperf_in_background(queue, **kwargs):
#     process = multiprocessing.Process(target=generate_iperf_traffic, args=(queue,), kwargs=kwargs)
#     process.start()
#     try:
#         yield
#     finally:
#         process.terminate()
#         process.join()
#
#
# @contextlib.contextmanager
# def run_instrument_in_background(queue, ps_ip, ps_parameters, terminate_flag):
#     # TODO 计算power最大值，1秒4次数据量
#     process = multiprocessing.Process(target=read_instrument, args=(queue, ps_ip, ps_parameters, terminate_flag))
#     process.start()
#     try:
#         yield
#     finally:
#         process.terminate()
#         process.join()


class TestRunnerBase(ABC):
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = load_yaml(config_path)
        # print(self.config)
        self.powers_ip = self.config["POWER_SENSOR_IP1"]
        self.powers_ip2 = self.config["POWER_SENSOR_IP2"]
        self.powers_parameters = self.config["POWER_SENSOR_PROFILE1"]
        self.powers_parameters2 = self.config["POWER_SENSOR_PROFILE2"]
        self.powers_profile = self.config["POWER_SENSOR_PROFILE1"]
        self.powers_profile2 = self.config["POWER_SENSOR_PROFILE2"]
        self.ue_and_cell_infos = self.config["UE_AND_CELL_INFOS"]
        self.bbu_ip = self.config["BBU_IP"]
        self.p_max = self.config["pMax"]
        self.traffic_queue = multiprocessing.Queue()
        self.instrument_queue = multiprocessing.Queue()
        self.db = DeviceDB()
        self.result = Result(self.db)
        self.terminate_flag = multiprocessing.Event()
        # self.ue = UETest(self.config_path)

        self.ue_login_info_list = UETest.get_ue_login_info(self.config)
        # print("ue login info: ",self.ue_login_info_list)



    def _attach_ue_and_return_info(self, ue_ips):
        """

        :param ue_ips:
        :return: list with tuple
        """
        attach_ues_info = []
        for i in range(1, len(ue_ips) + 1):
            # ue_acctch_pci_and_ip = self.ue.main(f"DDTT_UE_{i}")
            ue_acctch_pci_and_ip = UETest(self.config_path).main(f"DDTT_UE_{i}")
            attach_ues_info.append(ue_acctch_pci_and_ip)
            # print(f"UE ip:{ue_acctch_pci_and_ip[1]} attached to pci:{ue_acctch_pci_and_ip[0]}")
        print(attach_ues_info)
        return attach_ues_info
        # return ue_ip

    def validate_ue_ip(self,ue_info_from_ue):

        ue_info_from_config = set(self.config["UE_CELLULAR_IP"] + self.config["PCI"])
        # print("debug config ue info", ue_info_from_config)
        # print("debug attached ue info",ue_info_from_ue)

        assert ue_info_from_config == ue_info_from_ue, f"UE info do not match. UE info is now: {ue_info_from_ue}"


    def attach_ue_and_return_info(self):
        return {item for tup in self._attach_ue_and_return_info(self.config["UE_CELLULAR_IP"])
                for item in tup}


    def _ue_lock_cells(self,ue_ip,ue_port,ue_su_passwd,cell_pci,cell_ssb):
        iperf_manager = IperfManager(
            host=ue_ip,
            user='hguser',
            password="YOUR_SECRET",
            port=ue_port,
            su_password=ue_su_passwd
        )
        iperf_manager.setup_commands(pci=cell_pci, ssb=cell_ssb)


    def ue_lock_cells(self, ue_and_cell_infos):
        for ue_and_cell_info in ue_and_cell_infos:
            print(ue_and_cell_info)
            self._ue_lock_cells(**ue_and_cell_info)


    @staticmethod
    @abstractmethod
    def run(self):
        pass
        # try:
        #     traficc_profile = self.config["TRAFICC_PROFILE"]
        #     # self.validate_ue_ip()
        #     # TODO 添加其他异常检查
        #     # assert self.some_other_check(), "Some other check failed."
        #
        #     iperf_duration = self.calculate_iperf_duration(traficc_profile)
        #
        #     # debug
        #     # ps -eo pid,etime,args | grep 127.0.0.1
        #     iperf_duration = 120  # 最小1500
        #
        #     self.execute_tests(traficc_profile, iperf_duration)
        #     self.save_db_to_excel("_04_result.xlsx")
        #
        #
        #
        # except AssertionError as e:
        #     error_message = str(e)
        #     logger.error(f"AssertionError: {error_message}")
        #     # UE attch check
        #     if "IP addresses do not match" in error_message:
        #         print(f"AssertionError caught: {e} (IP Check)")
        #         # TODO teardown here
        #     # TODO 其他异常检查
        #     elif "Some other check failed" in error_message:
        #         print(f"AssertionError caught: {e} (Other Check)")
        #         # 在这里处理其他检查失败的错误，例如记录日志、执行其他逻辑等
        #     else:
        #         print(f"Unknown AssertionError caught: {e}")
        #         # 在这里处理未知的断言错误
        #
        # except PermissionError as e:
        #     logger.error(f"{e}")
        #
        # finally:
        #     try:
        #         self.teardown()
        #     except Exception as e:
        #         logger.error(f"teardown failed: {e}")

    @staticmethod
    @abstractmethod
    def calculate_iperf_duration(traficc_profile):
        pass

    @abstractmethod
    def execute_tests(self, traficc_profile, iperf_duration):
        pass

    def monitor_queues(self, iperf_duration,traficc_profile):
        start_time = time.time()
        while time.time() - start_time < iperf_duration:
            time.sleep(1)
            try:
                # there is taffice
                if not self.traffic_queue.empty():
                    self.handle_traffic_queue(traficc_profile)
            except KeyboardInterrupt:
                self.handle_keyboard_interrupt()
                break
        self.terminate_flag.set()
        # self.terminate_flag_t.set()
        # self.check_thread.join()


    def should_continue(self,s,d):
        # logger.info(f"time.time() - s < d:  f{time.time() - s} < {d}")
        return time.time() - s < d

    def handle_traffic_queue(self,traficc_profile):
        """
        Handle traffic and power data realtime
        :return: None
        """
        # TODO 实时power check
        last_warning_time = 0
        iperf_info_tup = self.traffic_queue.get()
        logger.info(f"iperf_pid: {iperf_info_tup}")
        traffic_p = iperf_info_tup[2]
        traficc_profile_timeout = traficc_profile["PROFILE_RUNNING_TIME"][traffic_p]*60 \
                                  + INSTRUMENT_PROFILE_TIMEOUT
        start_time = time.time()

        # 直到打流开始
        # 这里需要退出
        # while self.traffic_queue.empty():
        while self.traffic_queue.empty() and not self.terminate_flag.is_set() \
                and self.should_continue(start_time,traficc_profile_timeout):
            if not self.instrument_queue.empty():
                instrument_data = self.instrument_queue.get()
                logger.info(f"Got instrument data: {instrument_data}")
                if isinstance(instrument_data, (np.float32, str, np.float64)):
                    logger.info(f'instrument data: {instrument_data}')
                    self.db.insert_data(*iperf_info_tup, float(instrument_data))
                # two NRQ6 debug
                elif isinstance(instrument_data, (list, tuple)):
                    # print(iperf_info_tup, instrument_data, )
                    logger.info(f'instrument data: {instrument_data} with {iperf_info_tup}')
                elif isinstance(instrument_data, (dict, )):
                    # print(iperf_info_tup, instrument_data, )
                    # logger.info(f'instrument data: {instrument_data}')
                    self.db.insert_data(*iperf_info_tup,
                                        float(instrument_data['data_rms_mean']),
                                        f"{instrument_data['ip']} + {instrument_data['freq_ps']}")

            else:
                current_time = time.time()
                if current_time - last_warning_time >= 10:
                    # todo debug need check if instrument is down
                    # logger.info(f'instrument_queue is empty now')
                    last_warning_time = current_time
            time.sleep(0.1)


            # TODO 时间到执行下面
            # no need
            # self.terminate_flag.set()




    def handle_keyboard_interrupt(self):
        print("Main process received KeyboardInterrupt, terminating...")
        self.terminate_flag.set()

    def save_db_to_excel(self, excel_path):
        self.db.save_db_to_excel(excel_path)

    def teardown(self):
        """Perform cleanup operations."""
        if self.db:
            self.db.close()
        self.terminate_flag.set()


# class IperfTestRunner(TestRunnerBase):
#     @staticmethod
#     def calculate_iperf_duration(traficc_profile):
#         run_time = traficc_profile["RUNTIME"]
#         iperf_duration = run_time * 60 * 60 + 60 * 5
#         return iperf_duration
#
#     def execute_tests(self, traficc_profile, iperf_duration):
#         with run_iperf_in_background(self.traffic_queue, **traficc_profile):
#             with run_instrument_in_background(self.instrument_queue, self.powers_ip, self.powers_parameters,
#                                               self.terminate_flag):
#                 self.monitor_queues(iperf_duration)
#
#     def run(self):
#         try:
#             traficc_profile = self.config["TRAFICC_PROFILE"]
#             # UE attach检查
#             # self.validate_ue_ip()
#             # TODO 添加其他异常检查
#             # assert self.some_other_check(), "Some other check failed."
#             # 测试时间
#             test_duration = self.calculate_iperf_duration(traficc_profile)
#
#             # start debug
#             test_duration = 120  # 最小1500s
#             # end debug
#
#             self.execute_tests(traficc_profile, test_duration)
#             # self.save_db_to_excel("result/result.xlsx")
#             self.result.save_db_to_excel("result/result.xlsx")
#             # TODO result 处理
#
#
#         except AssertionError as e:
#             error_message = str(e)
#             logger.error(f"AssertionError: {error_message}")
#             # UE attch check
#             if "IP addresses do not match" in error_message:
#                 print(f"AssertionError caught: {e} (IP Check)")
#                 # TODO teardown here
#             # TODO 其他异常检查
#             elif "Some other check failed" in error_message:
#                 print(f"AssertionError caught: {e} (Other Check)")
#                 # 在这里处理其他检查失败的错误，例如记录日志、执行其他逻辑等
#             else:
#                 print(f"Unknown AssertionError caught: {e}")
#                 # 在这里处理未知的断言错误
#
#         except PermissionError as e:
#             logger.error(f"{e}")
#
#         finally:
#             try:
#                 self.teardown()
#             except Exception as e:
#                 logger.error(f"teardown failed: {e}")
#
#
# class TestRunnerFactory:
#     @staticmethod
#     def create_test_runner(config_path):
#         config = load_yaml(config_path)
#         if not config:
#             raise ValueError(f"Unable to load configuration from {config_path}")
#         test_type = config.get("TEST_TYPE", "iperf")
#         if test_type == "iperf":
#             return IperfTestRunner(config_path)
#         else:
#             raise ValueError(f"Unknown test type: {test_type}")


# if __name__ == '__main__':
#     runner = TestRunnerFactory.create_test_runner("main_config.yaml")
#     runner.run()

    # UTE_UE_CONFIG = load_yaml("main_config.yaml")
