import logging
import os
from time import sleep
from pyvisa import ResourceManager
from pyvisa.resources import MessageBasedResource
from .utility.definition import *
from .utility.utilityLib import process_array_with_frameLength
import numpy
import numpy as np
import warnings
from pyvisa.errors import VisaIOWarning



warnings.filterwarnings("ignore", category=VisaIOWarning)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


default_parameters = {
    "freq_ps": 2145.1,
    "bandwidth_ps": 10.0,
    "loss_ps": 45.25,
    "att_ps": 30.0,
}


def findRBW(rbwMHz: float):
    rbwList = np.array([
        0.0001, 0.0002, 0.0003, 0.0005,
        0.001, 0.002, 0.003, 0.005,
        0.01, 0.02, 0.03, 0.05,
        0.1, 0.2, 0.3, 0.5,
        1, 2, 3, 5,
        10, 20, 40, 80, 100
    ])
    minRBW = np.min(rbwList)
    maxRBW = np.max(rbwList)
    if rbwMHz < minRBW:
        retRBW = minRBW
    elif rbwMHz > maxRBW:
        retRBW = maxRBW
    else:
        retRBW = min(delta for delta in (rbwList - rbwMHz) if delta >= 0) + rbwMHz
    return retRBW


def setup_debug(session: MessageBasedResource, **parameters_ps):
    parameters = default_parameters.copy()
    parameters.update(parameters_ps)
    session.write(f'*RST;*CLS;')
    sleep(1)
    session.write(f'*ESE 61;')
    session.query(f':FUNC "XTIM:POW";*OPC?;')
    session.write(f':FREQ:CENT {parameters.get(PowerSensorParameters.freq_ps.value) * 1e6};')
    session.write(f':UNIT:POW DBM;')
    session.write(f':AVER:TYPE POW;')
    session.write(f':AVER:TCON REP;')
    session.write(f':AVER ON;')
    session.write(f':AVER:COUN 1;')
    session.write(f':BAND:RES:TYPE:AUTO OFF;')
    session.write(f':BAND:RES:TYPE FLAT;')
    session.write(f':BAND:TYPE RES;')
    session.write(f':BAND:RES {findRBW(parameters.get(PowerSensorParameters.bandwidth_ps.value)) * 1e6};')
    session.write(f':TRAC:TIME {0.2};')
    session.write(f':TRAC:POIN {1024};')
    session.write(f':CORR:OFFS:STAT ON;')
    session.write(f':CORR:OFFS {parameters.get(PowerSensorParameters.loss_ps.value)}')
    session.write(f':INP:ATT:AUTO OFF;')
    attMsg = ':INP:ATT 30' if parameters.get(PowerSensorParameters.att_ps.value) > 0.1 else ':INP:ATT 0'
    session.write(attMsg)
    session.write(f':TRIG:SOUR IMM;')
    session.write(f':INIT:CONT ON;')
    err = session.query('SYST:ERR?').strip()
    if err != '0,"No error"':
        msg = f'setup error : {err}'
        logger.exception(msg)
        raise Exception(msg)


def readBlock(session: MessageBasedResource):
    """
    #44105AVGf41024
    """
    session.write(':TRAC:DATA?')
    rawData = session.read_bytes(break_on_termchar=True, count=50 * 1024, chunk_size=50 * 1024)
    binaryArrayflag = chr(rawData[0])
    if binaryArrayflag != '#':
        logger.exception(f'invalid binary data array for R&S NRQ6')
        return
    binaryLengthIndicator = int(chr(rawData[1]))

    dataLength = (int(rawData[2: binaryLengthIndicator + 2].decode('ascii')) - 5 - binaryLengthIndicator) // int(
        chr(rawData[binaryLengthIndicator + 6]))
    dataIndex = binaryLengthIndicator + len(str(dataLength)) + 7

    return np.frombuffer(rawData[dataIndex:-1], dtype='f')


def run(session, profile=None):
    session.timeout = 10000

    # 两个NRQ6 调试
    # '''
    try:
        setup_debug(session, **profile)

    except Exception as err:
        # raise # debug need
        try:
            session.close()
            # raise  # debug 需要
        except Exception as err:
            pass
    except SystemExit as e:
        print(f"Caught SystemExit: {e}")
        raise
    # '''

    try:
        data_rms = readBlock(session)
        # data_rms_mean = np.mean(data_rms)
        data_rms_mean = np.max(data_rms)

        session.close()
        # rm.close()
        return data_rms_mean

        # TODO init array for array remainder
        overshot_rms_array_remain = np.array([], dtype=np.double)
        overshot_max_rms_array_remain = np.array([], dtype=np.double)
        overshot_rms_array = data_rms - parameters.get(PowerSensorParameters.power_rms_ps.value)
        overshot_max_rms_array = data_rms - parameters.get(PowerSensorParameters.power_max_rms_ps.value)
        # TODO get real array
        overshot_rms_array = np.append(overshot_rms_array_remain, overshot_rms_array)
        # TODO new max value
        max_rms_value = np.max(overshot_rms_array) + parameters.get(
            PowerSensorParameters.power_rms_ps.value)
        overshot_max_rms_array = np.append(overshot_max_rms_array_remain, overshot_max_rms_array)
        overshot_rms_array_new, overshot_rms_array_remain, overshot_rms_resolution = process_array_with_frameLength(
            overshot_rms_array,
            1,  # frameLength
            5,  # resolution
            "TDD")  # self.duplex.value
        data_rms_for_plot = overshot_rms_array_new + parameters.get(
            PowerSensorParameters.power_rms_ps.value)
        # print("data_rms_for_plot:",data_rms_for_plot)
        return data_rms_for_plot


    except Exception as err:
        try:
            session.close()
        except Exception as err:
            pass
        # logger.exception(f'nrq process err: {err}')
        raise
    except SystemExit as e:
        print(f"Caught SystemExit: {e}")
        raise


def run_powersensor(ip, profile=None):
    rm = ResourceManager()
    resourceName = f'TCPIP0::{ip}::INSTR'
    session = rm.open_resource(resource_name=resourceName)
    try:

        # start debug
        # import numpy as np
        # data_rms = [1, 2, 3, 4, 5]
        # data_rms_mean = np.mean(data_rms)
        # idn = session.query('*IDN?')
        # print(idn)

        # [3.0, '127.0.0.1', {'freq_ps': 2145.1, 'bandwidth_ps': 10.0, 'loss_ps': 45.25, 'att_ps': 30.0}]
        # return [data_rms_mean, ip, profile]

        # {'data_rms_mean': 3.0, 'ip': '127.0.0.1', 'freq_ps': 2145.1, 'bandwidth_ps': 10.0, 'loss_ps': 45.25, 'att_ps': 30.0}
        # return {
        #     'data_rms_mean': data_rms_mean,
        #     'ip': ip,
        #     **profile
        # }
        # end debug


        data_rms_mean = run(session, profile)
        return {
            'data_rms_mean': data_rms_mean,
            'ip': ip,
            **profile
        }

        data_rms_mean = run(session, profile)
        return data_rms_mean

        # return run(session, profile)

    finally:
        # session.close()
        rm.close()


# if __name__ == '__main__':
#     # 1
#     ip = "127.0.0.1"
#     parameters = {
#         "freq_ps": 3795,  # 中心频点
#         "bandwidth_ps": 10,  # 带宽
#         "loss_ps": 32,  # 设置校正偏移值
#     }
#     res = run_powersensor(ip, parameters)
#     print(res)
#
#     # 2
#     ip = "127.0.0.1"
#     parameters = {
#         "freq_ps": 3415.02,  # 中心频点
#         "bandwidth_ps": 10,  # 带宽
#         "loss_ps": 32,  # 设置校正偏移值
#     }
#     res = run_powersensor(ip, parameters)
#     print(res)
