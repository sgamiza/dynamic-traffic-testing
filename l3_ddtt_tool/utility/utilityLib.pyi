from typing import Tuple
import numpy as np

def delay(delay: float) -> None:...
    # just sleep some seconds

def consecutive_overshot_measure(input_data: np.array, last_pos_value_length: int) -> Tuple[int, np.ndarray]:...
    # This funciton is to analyze input data and get the consecutive positive value length array
    # @input_data: new data from instrument trace
    # @last_pos_value_length: last pos value array length

    # return:
    # 1. last_pos_value_length
    # 2. overshort_array

def overlap_check(lastdata: np.ndarray, currentdata: np.ndarray) -> int:...
    # This function will find the overlap array between last data and current data
    # @lastdata: last array
    # @currentdata: current array
    # return:
    # overlap index in current data

def process_array_with_frameLength(dataArray: np.ndarray, frameLengthMs: float, resolutionMs: float, duplex: str = 'FDD or TDD') -> Tuple[np.ndarray, np.ndarray, float]:...
    #This function will split whole array based on the frameLengthMs
    # return 1: max value array of the splitted frame circle value array
    # return 2: remain raw data points
    # return 3: section length (ms)
	
