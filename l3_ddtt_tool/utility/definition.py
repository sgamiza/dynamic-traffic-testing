
from enum import Enum
from dataclasses import dataclass


class PowerSensorDevice(Enum):
    NRQ6 = 'R&S NRQ6'


class PowerSensorParameters(Enum):
    # comboBox_ps = 'comboBox_ps'
    lineEdit_ip_ps = 'lineEdit_ip_ps'
    power_ps = 'power_ps'
    bandwidth_ps = 'bandwidth_ps'
    freq_ps = 'freq_ps'
    loss_ps = 'loss_ps'
    att_ps = 'att_ps'
    power_rms_ps = 'power_rms_ps'
    time_power_rms_ps = 'time_power_rms_ps'
    power_max_rms_ps = 'power_max_rms_ps'
    time_power_max_rms_ps = 'time_power_max_rms_ps'
    power_peak_ps = 'power_peak_ps'
    time_power_peak_ps = 'time_power_peak_ps'
    # radioButton_power_ps = 'radioButton_power_ps'


@dataclass
class PipeParameters(object):
    pipe: int
    para: dict
    running: bool
    zeroSpanSpurDevice: bool
    ZeroSpanPowerDevice: bool
    powerSensorDevice: bool
    zeroSpanPowerTestCase: bool
    zeroSpanSpurTestCase: bool
    powerSensorPowerTestCase: bool


@dataclass
class PipeParametersArray(object):
    flagArray: list[PipeParameters]


if __name__ == '__main__':
    pArray = PipeParametersArray([])
    enableFlag = PipeParameters(1, {}, False, False, False, False, False, False, False)
    pArray.flagArray.append(enableFlag)
    vdict = {"name": "VENDOR"}
    for item in pArray.flagArray:
        if item.pipe == 1:
            item.powerSensorDevice = True
            item.para = vdict
            break
    print(pArray.flagArray)
