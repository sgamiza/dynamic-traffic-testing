# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""

import os

from .optional_lab import ue_lib



class UETest:
    def __init__(self, config_path):
        # from ddtt_base import load_yaml
        # self.ue_info_list = []
        self.config_path = config_path
        # from ddtt_base import load_yaml
        # self.config_args = load_yaml(config_path)
        # self._get_ue_info()
        # UTE_UE_CONFIG = load_yaml("main_config.yaml")
        # ue_ip_from_config = UTE_UE_CONFIG["UE_CELLULAR_IP"]
        # pci_from_config = UTE_UE_CONFIG["PCI"]
        # print(ue_ip_from_config)
        # print(pci_from_config)
        # print(set(pci_from_config+ue_ip_from_config))



        self.api = ue_lib.PythonApi(config_path=config_path)
        self.ue = None

    def require_and_attach_ue(self, capabilities="DDTT"):
        try:
            # print("debug:",f"TEST_UE_Alias_{capabilities} ",self.api)
            self.ue = self.api.require_ue(f"TEST_UE_Alias_{capabilities}",
                                          capabilities=[capabilities])  # UE reservation
            self.ue.detach()
            self.ue.attach()
        except Exception as e:
            print(f"Error while requiring or attaching UE: {e}")
            self.cleanup()
            raise

    def get_ue_info(self):
        try:
            re = self.ue.get_ue_info(info_list='ALL')
            return re["pci"], re["ip"]
        except Exception as e:
            print(f"Error while getting UE info: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        if self.ue:
            self.ue.shutdown()
        if self.api:
            self.api.shutdown()  # Test Suite teardown

    def main(self, capabilities):
        try:
            self.require_and_attach_ue(capabilities)
            pci, ip = self.get_ue_info()
            print(pci, ip)
            self.ue.shutdown()  # Release UE
            return pci, ip
        except Exception as e:
            print(f"Error in main execution: {e}")
            self.cleanup()
            raise
        finally:
            self.cleanup()


    @staticmethod
    def initialize_api():
        # 从环境变量中获取配置文件路径
        config_path = os.environ.get("ABSTRACT_LIB_CONFIG")
        if not config_path:
            raise ValueError("Environment variable ABSTRACT_LIB_CONFIG is not set")
        return config_path


    @staticmethod
    def get_ue_login_info(config_args):
        ue_login_info_list = []
        ue_pools = config_args.get('UE_POOLS', {})
        for pool_name, pool in ue_pools.items():
            inline_config = pool.get('inline_config', {})
            for ue_name, ue_config in inline_config.items():
                ue_pc_address = ue_config.get('CONSTRUCTOR_PARAMETERS', {}).get('configuration', {}).get(
                    'ue_pc_address')
                root_password = ue_config.get('CONSTRUCTOR_PARAMETERS', {}).get('root_password')
                if ue_pc_address and root_password:
                    ue_login_info_list.append({
                        'ue_pc_address': ue_pc_address,
                        'root_password': root_password
                    })

        return ue_login_info_list




# if __name__ == '__main__':
#     test = UETest(r"main_config.yaml")
#     test.main(f"DDTT_UE_1")
#     # print(UETest.initialize_api())
