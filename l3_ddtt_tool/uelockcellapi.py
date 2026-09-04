# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""
import logging
import time
from .iperobj import IPERF_OBJ


# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IperfManager:
    def __init__(self, host, user, password, port=2200, su_password=None):
        self.my_iperf = IPERF_OBJ(host, user, password, port)
        self.su_password = su_password

    def run_command(self, command):
        logger.info(f"Command : {command}")
        response = self.my_iperf.channel_cmd(command)
        # print(response)
        time.sleep(0.5)
        return response

    def check_status(self, response):
        return "success" in response.lower()

    def is_root(self, response):
        # 检查返回结果中是否包含root目录的内容
        if "bin" in response and "root" in response and "proc" in response:
            return True
        if "Permission denied" in response:
            return False
        return False

    def setup_commands(self, pci, ssb):
        # Initial commands
        commands = [
            "ls",
            "su"
        ]

        for cmd in commands:
            response = self.run_command(cmd)
            if cmd == "su" and self.su_password:
                response = self.run_command(self.su_password)
            if cmd == "ls" and self.is_root(response):
                print("Entered root environment.")
                break

        # 删除命令
        for cell in range(1, 10):
            response = self.run_command(f"cfgcli del InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.NR5GRanCell.{cell}.")

            if not self.check_status(response):
                print(f"Command failed: {response}")

        # 配置命令
        config_commands = [
            ("cfgcli -G InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.", 1),
            ("cfgcli add InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.NR5GRanCell.", 2),
            (f"cfgcli -s InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.NR5GRanCell.1.PhysicalCellID {pci}", 3),
            (f"cfgcli -s InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.NR5GRanCell.1.Downlink-NR-ARFCN {ssb}", 4),
            ("cfgcli -G InternetGatewayDevice.WANDevice.2.X_ALU-COM_Cellular.Interface.1.X_ALU-COM_5GRanCells.NR5GRanCell.1.", 5)
        ]

        for cmd, index in config_commands:
            print(f"{index}*" * 60)
            response = self.run_command(cmd)
            # # ue 返回需要encode
            # print("response:",response.encode('utf-8'))
            if not self.check_status(response):
                logger.error(f"Command {index} failed: {response}")

        time.sleep(1)
        # self.run_command("reboot")
        # time.sleep(300)


# if __name__ == '__main__':
#
#     iperf_manager = IperfManager(
#         host="127.0.0.1",
#         user='hguser',
#         password="YOUR_SECRET",
#         port=2200,
#         su_password="YOUR_SECRET"
#     )
#     iperf_manager.setup_commands(pci=18, ssb=639936)
