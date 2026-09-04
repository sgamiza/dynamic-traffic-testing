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
import queue
import subprocess

import logging
import contextlib
import threading
import signal
from .bbuapi import BBUAlarmManager, AlarmThread
from .ddtt_base import (load_yaml, generate_iperf_traffic,
                       read_instrument, TestRunnerBase)

from .utility.settings import configure_logging
INSTRUMENT_DURATION_TIMEOUT = 3600*8

# # Configure logging
# logger = logging.getLogger('pyvisa')
# logger.setLevel(logging.ERROR)
# logger = logging.getLogger('paramiko.transport')
# logger.setLevel(logging.ERROR)
#
# # setup logging
# iperf_logpath = os.path.join(os.getcwd(), 'logs')
# if not os.path.isdir(iperf_logpath):
#     os.makedirs(iperf_logpath)
# test_date = str(datetime.datetime.now().strftime('_%m%d%Y_%I%M%S'))
# gLogName = os.path.basename(sys.argv[0]) + test_date + '.log'
# gLogName = os.path.join(iperf_logpath, gLogName)
#
# logging.basicConfig(filename=gLogName, format='%(funcName)s %(levelname)s | %(asctime)s | %(message)s',
#                     datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
# logFormatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
#
# logger = logging.getLogger(__name__)
# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# logger.addHandler(consoleHandler)


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@contextlib.contextmanager
def run_iperf_in_background(queue, **kwargs):
    process = multiprocessing.Process(target=generate_iperf_traffic, args=(queue,), kwargs=kwargs)
    process.start()
    try:
        yield
    finally:
        process.terminate()
        process.join()


def terminate_after_duration(p, d):
    time.sleep(d)
    # p.terminate() # multiprocessing.Process
    # 函数和类必须是可以被 pickle 序列化的
    kill_process(p)  # pid


def kill_process(pid):
    try:
        if os.name == 'nt':
            try:
                # os.system(f"taskkill /F /PID {pid}")
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except:
                pass
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")


@contextlib.contextmanager
def run_instrument_in_background(queue, ps_ip, ps_parameters, terminate_flag):
    # TODO 计算power最大值，1秒4次数据量
    process = multiprocessing.Process(target=read_instrument, args=(queue, ps_ip, ps_parameters, terminate_flag))
    process.start()

    # TODO
    duration = 3600

    # TODO 坑
    # 启动一个进程在指定时间后终止子进程
    # 函数和类必须是可以被 pickle 序列化的，这意味着它们不能是嵌套函数或局部函数
    # 移动到全局作用域
    # def terminate_after_duration(p, d):
    #     time.sleep(d)
    #     p.terminate()
    terminator = multiprocessing.Process(target=terminate_after_duration,
                                         args=(process.pid, INSTRUMENT_DURATION_TIMEOUT))
    terminator.start()

    try:
        yield process.pid
    finally:
        terminate_flag.set()
        process.terminate()
        process.join()

        # 启动一个进程在指定时间后终止子进程
        terminator.terminate()
        terminator.join()


class IperfTestRunner(TestRunnerBase):
    def __init__(self, config_path):
        super().__init__(config_path)
        self.terminate_flag_t = threading.Event()
        self.check_thread = None
        self.exception_queue = queue.Queue()
        # self.iperf_specific_setup()

    @staticmethod
    def calculate_iperf_duration(traficc_profile):
        run_time = traficc_profile["RUNTIME"]
        iperf_duration = run_time * 60 * 60 + 60 * 5
        return iperf_duration

    # def execute_tests(self, traficc_profile, iperf_duration):
    #     with run_iperf_in_background(self.traffic_queue, **traficc_profile):
    #         with run_instrument_in_background(self.instrument_queue, self.powers_ip, self.powers_parameters,
    #                                           self.terminate_flag):
    #             self.monitor_queues(iperf_duration)

    def execute_tests(self, traficc_profile, iperf_duration, instrument_configs):
        """

        :param traficc_profile:
        :param iperf_duration:
        :param instrument_configs:
        :return:
        """
        # print("bbu ip is:",self.bbu_ip)
        self.start_bbu_alarm_check(self.bbu_ip, self.terminate_flag_t,self.exception_queue)

        logger.info("Starting iperf in background")
        with run_iperf_in_background(self.traffic_queue, **traficc_profile):
            logger.info("Starting instruments in background")
            with contextlib.ExitStack() as stack:
                # kill pids
                pids = []
                # 初始化 terminate_flag
                self.terminate_flag = multiprocessing.Event()
                for config in instrument_configs:
                    pid = stack.enter_context(run_instrument_in_background(
                        self.instrument_queue,
                        config['ps_ip'],
                        config['ps_parameters'],
                        self.terminate_flag
                    ))
                    pids.append(pid)

                # TODO 进程处理
                # check bbu alarm
                # 方式1
                # ip_to_check = '127.0.0.1'  # TEST_DUT stability
                # def check_alarm(ip, terminate_flag):
                #     alarm_manager = BBUAlarmManager(ip)
                #     while not terminate_flag.is_set():
                #         alarm_manager.connect().run()
                #         time.sleep(60)
                #     alarm_manager.disconnect()
                #
                # check_thread = threading.Thread(target=check_alarm, args=(ip_to_check, self.terminate_flag))
                # check_thread.start()

                # 进程处理
                logger.info("Monitoring queues...")
                self.monitor_queues(iperf_duration, traficc_profile)

        #     logger.info("Exited instrument managers")
        # logger.info("Exited iperf manager")

        # TODO
        # 终止所有子进程
        for pid in pids:
            kill_process(pid)

        self.progress_bbu_alarm()



    def start_bbu_alarm_check(self,bbu_ip,flag,exception):
        logger.info("Starting alarm check")
        self.check_thread = AlarmThread(bbu_ip, flag, exception)
        self.check_thread.start()


    def progress_bbu_alarm(self):
        self.terminate_flag_t.set()
        self.check_thread.join()
        # alarm 线程结束
        exception_list = []
        while not self.exception_queue.empty():
            try:
                exception = self.exception_queue.get(timeout=1)
                exception_list.append(exception)
            except queue.Empty:
                pass
        # 处理完队列后保存异常到文件
        self.post_process_bbu_alarm(exception_list)

    def post_process_bbu_alarm(self, exception_list, exception_file="bbulog/exception_log.txt"):
        with open(exception_file, "w") as file:
            for exception in exception_list:
                file.write(f"{exception}\n")

        if exception_list:
            # TODO if need runtime
            assert False, f"Alarm Exception: {exception_list}"



    def run(self):
        try:
            traficc_profile = self.config["TRAFICC_PROFILE"]
            test_duration = self.calculate_iperf_duration(traficc_profile)

            # need load from config
            # ue_and_cell_infos = [
            #     # UE 127.0.0.1
            #     {"ue_ip": "127.0.0.1",
            #      "ue_port": 2203,
            #      "ue_su_passwd": "YOUR_SECRET",
            #      "cell_pci": 271,
            #      "cell_ssb": 627648,
            #      # "cell_pci": 272,
            #      # "cell_ssb": 652992,
            #      },
            #     # UE 127.0.0.1
            #     {"ue_ip": "127.0.0.1",
            #      "ue_port": 2204,
            #      "ue_su_passwd": "YOUR_SECRET",
            #      # "cell_pci": 271,
            #      # "cell_ssb": 627648,
            #      "cell_pci": 272,
            #      "cell_ssb": 652992,
            #      },
            # ]

            # print(self.ue_and_cell_infos)
            # print(ue_and_cell_infos)

            # need load from config
            instrument_configs = [
                # NRQ6 127.0.0.1
                {
                    'ps_ip': self.powers_ip,
                    # 'ps_parameters': self.powers_parameters
                    'ps_parameters': self.powers_parameters
                },
                # NRQ6 127.0.0.1
                {
                    'ps_ip': self.powers_ip2,
                    'ps_parameters': self.powers_parameters2
                }
            ]

            # print(instrument_configs[0]['ps_parameters'])
            # print(self.powers_parameters)
            # print()
            # print(instrument_configs[1]['ps_parameters'])
            # print(self.powers_parameters2)

            # start debug config
            # os.environ['DEBUGGING'] = '1'
            # test_duration = 120
            # self._ue_lock_cells("127.0.0.1",2200,"YOUR_SECRET",18,639936)
            # end debug config

            """start testing"""
            self.ue_lock_cells(self.ue_and_cell_infos)
            ues_info = self.attach_ue_and_return_info()
            self.validate_ue_ip(ues_info)

            # TODO assert self.some_other_check(), "Some other check failed."

            self.execute_tests(traficc_profile, test_duration, instrument_configs)
            error_power = self.result.save_db_to_excel("result/result.xlsx",self.p_max)
            # error_power = self.result.save_db_to_excel("result/result.xlsx",-28)
            # TODO result 处理

            if not error_power:
                return True,
            else:
                return False, \
                       f'there are {len(error_power)} data Exceeding power threshold,\r' \
                       f'please check {os.path.abspath("result/result.xlsx")}'

            # return True,

        except AssertionError as e:
            error_message = str(e)
            logger.error(f"AssertionError: {error_message}")
            # UE attch check
            if "UE info do not match" in error_message:
                print(f"AssertionError caught (UE Check): {e}")
                # TODO teardown here
                return False, \
                    f'UE atach failed: {error_message} .'
            elif "Alarm Exception" in error_message:
                print(f"AssertionError caught (Alarm Check): {e}")
                return False, error_message
            else:
                print(f"Unknown AssertionError caught: {e}")
                # 在这里处理未知的断言错误

        except PermissionError as e:
            logger.error(f"{e}")

        finally:
            try:
                self.teardown()
            except Exception as e:
                logger.error(f"teardown failed: {e}")


class TestRunnerFactory:
    @staticmethod
    def create_test_runner(config_path):
        config = load_yaml(config_path)
        if not config:
            raise ValueError(f"Unable to load configuration from {config_path}")
        test_type = config.get("TEST_TYPE", "iperf")
        if test_type == "iperf":
            return IperfTestRunner(config_path)
        else:
            raise ValueError(f"Unknown test type: {test_type}")


# if __name__ == '__main__':
#     runner = TestRunnerFactory.create_test_runner("main_config.yaml")
#     result = runner.run()
#     print(result)
#
#     # UTE_UE_CONFIG = load_yaml("main_config.yaml")
#     # ue_ip_from_config = UTE_UE_CONFIG["UE_CELLULAR_IP"]
#     # UE_POOLS = UTE_UE_CONFIG["UE_POOLS"]["ExampleUePool"]["inline_config"]
