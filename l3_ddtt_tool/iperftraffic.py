import datetime
import sys
import time
import logging
import os
from random import randint
from .iperobj import IPERF_OBJ

test_date = str(datetime.datetime.now().strftime('_%m%d%Y_%I%M%S'))

gLogger = logging.getLogger(__name__)


def show_remaining_time(wait_time):
    t_remaining = wait_time
    while t_remaining >= 0:
        # sys.stdout.write("%d \r" % t_remaining) # 显示不正常
        sys.stdout.write("\r %d " % t_remaining)
        sys.stdout.flush()
        t_remaining = t_remaining - 1
        time.sleep(1)
    sys.stdout.write("\n")


def get_bandwidth_rate(tech, bw, mimo, mod, lte_rate):
    bandwidth_rates = {
        '5G_FDD': {
            '20M': 160, '15M': 120, '10M': 80, '25M': 200, '30M': 240,
            '35M': 280, '40M': 333, '50M': 420, '5M': 42
        },
        '5G_TDD': {
            '100M': 570, '80M': 400, '60M': 340, '50M': 290, '40M': 230,
            '30M': 170, '20M': 111, '15M': 85, '10M': 52, '5M': 25
        },
        'LTE': {
            '20M': 150, '15M': 110, '10M': 75, '5M': 36
        }
    }

    if bw.endswith('HZ'):
        bw = bw[:-2]
    tech_type = None
    if '5G' in tech:
        if 'FDD' in tech:
            tech_type = '5G_FDD'
        elif 'TDD' in tech:
            tech_type = '5G_TDD'
    else:
        tech_type = 'LTE'
    b = bandwidth_rates.get(tech_type, {}).get(bw, 0)

    if '256' in mod:  # default  64QAM 6比特，256 8比特
        b += b // 3

    if '4x4' in mimo.lower():  # default 2*2
        b *= 2


    if b == 0:
        return 'ERROR'
    else:
        return b + lte_rate


def get_elapsed_time(t_start):
    elapsed = time.time() - t_start
    hours = elapsed / 3600
    minutes = (elapsed % 3600) / 60
    seconds = (elapsed % 3600) % 60
    return hours, minutes, seconds


def run_traffic_model(model, t_run, server_ip, port, bw, logname, iperf_ver, ue_ip, queue):
    """

    :param model:     profile
    :param t_run:     profile_running_time
    :param server_ip: iperf server
    :param port:      iperf port
    :param bw:
    :param logname:
    :param iperf_ver:
    :param ue_ip:
    :param queue:
    :return:
    """
    start_time = time.time()
    t_run = int(t_run * 60)
    if 'extreme_70' in model:
        t_traffic = 14  # seconds
        t_idle = 6  # seconds
    elif 'extreme_50' in model:
        t_traffic = 20  # seconds
        t_idle = 20  # seconds
    elif 'short' in model:
        t_idle = 3  # seconds
    elif 'resource' in model:
        load = int(int(model.split('_')[1]) * 0.95)
        bw = int(bw * load / 100)
        t_traffic = 25  # seconds
        t_idle = 5  # seconds

    try:
        my_iperf = IPERF_OBJ(server_ip, 'TEST_USER')
        t_elapsed = 0
        t_start = time.time()
        while t_elapsed < t_run:
            if 'short' in model:
                t_traffic = randint(1, 5)
            elif model == 'profile_50':
                t_traffic = randint(10, 120)
                t_idle = t_traffic
            elif model == 'profile_70':
                t_traffic = int(randint(1, 30) * 10 * 0.7)
                t_idle = int(t_traffic / 0.7 * 0.3)
            elif model == 'profile_30':
                t_traffic = int(randint(1, 30) * 10 * 0.3)
                t_idle = int(t_traffic / 0.3 * 0.7)
            elif model == 'profile_10':
                t_traffic = int(randint(1, 30) * 10 * 0.1)
                t_idle = int(t_traffic / 0.1 * 0.9)
            elif model == 'profile_100':
                t_traffic = t_run
                t_idle = 3

            gLogger.info("\n==========================\n"
                         "Start of running %s traffic model at %s" % (
                             model, datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S")))
            print(f"profile: {model},traffic_time: {t_traffic},idle_time: {t_idle}")

            if isinstance(ue_ip, (str,)):
                single_ue_trafiic(my_iperf, server_ip, ue_ip, port, bw, t_traffic, logname, iperf_ver)
                time.sleep(0.5)
                my_iperf.get_iperf_pid(ue_ip, (model, bw), queue)
            elif isinstance(ue_ip, (tuple, list)):
                for one_ue_ip in ue_ip:
                    single_ue_trafiic(my_iperf, server_ip, one_ue_ip, port, bw, t_traffic, logname, iperf_ver)
                time.sleep(0.5)
                my_iperf.get_iperf_pids(ue_ip, (model, bw), queue)
            # try:
            #     # trafic will not waite here
            #     my_iperf.run_iperf_for_download(ue_ip, port, bw, t_traffic, logname, iperf_ver)
            # except:
            #     # try to release ssh connection and re-establish again
            #     my_iperf.close_connection()
            #     time.sleep(3)
            #     my_iperf = IPERF_OBJ(server_ip, 'TEST_USER')
            #     my_iperf.run_iperf_for_download(ue_ip, port, bw, t_traffic, logname, iperf_ver)
            # time.sleep(1)

            gLogger.info("Profile: %s - Iperf traffic on going... Please wait for completion in %d seconds. " % (
            model, t_traffic))
            print('Remaining time: ')
            show_remaining_time(t_traffic)

            t_elapsed = time.time() - t_start
            if t_elapsed < t_run - t_idle:
                gLogger.info(
                    "Start of idle period - Please wait for the next traffic to start... remaining time (sec): %d" % t_idle)
                show_remaining_time(t_idle)

        my_iperf.close_connection()
        elapsed_hours, elapsed_minutes, elapsed_seconds = get_elapsed_time(start_time)
        gLogger.info("\n==========================\nCompletion of running %s traffic model at %s" % (
            model, datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S")))
        gLogger.info("Total Elapsed Time:   %dH : %dM : %dS" % (elapsed_hours, elapsed_minutes, elapsed_seconds))

    except Exception as e:
        gLogger.error(e)
        raise


def single_ue_trafiic(my_iperf, server_ip, ue_ip, port, bw, t_traffic, logname, iperf_ver):
    try:
        # trafic will not waite here
        my_iperf.run_iperf_for_download(ue_ip, port, bw, t_traffic, logname, iperf_ver)
    except:
        # try to release ssh connection and re-establish again
        my_iperf.close_connection()
        time.sleep(3)
        my_iperf = IPERF_OBJ(server_ip, 'TEST_USER')
        my_iperf.run_iperf_for_download(ue_ip, port, bw, t_traffic, logname, iperf_ver)

    # time.sleep(0.5)
    # my_iperf.get_iperf_pid(ue_ip, (model, bw), queue)


def run_iper_trafic(queue, **kwargs):
    """
    ####################################################################################################
    # User Settings:   The following parameters should be updated correctly before running the script  #
    ####################################################################################################
    radio = 'AHEGHA'  # 5G-FDD , 5G-TDD, LTE-FDD , LTE-TDD
    SERVER_IP = '127.0.0.1'  # IPERF Server IP address for running Iperf
    iperf_version = 'V2'  # 'V3' if want to run with iperf3
    technology = '5GSA-TDD'  # 5GNSA-FDD , 5GNSA-TDD, 5GSA-FDD, 5GSA-TDD, LTE-FDD , LTE-TDD
    carrier_bw = '10MHz'  # 20MHz , 15MHz , 10MHz, 5MHz, 30MHz , 40MHz , 50MHz , 100MHz
    mimo = '2x2MIMO'  # 2x2MIMO , 4x4MIMO
    modulation = '256QAM'  # 64QAM , 256QAM
    LTE_bitrate = 18  # If test 5GNSA, put here the expected bitrate for the LTE anchor carrier.
    runtime = 50  # hours
    t_idle_bw_profile = 3  # minutes
    t_idle_bw_seq = 7  # minutes

    #########################
    # End of User Settings  #
    #########################
    """
    radio = kwargs.get('RADIO')
    SERVER_IP = kwargs.get('SERVER_IP')
    iperf_version = kwargs.get('IPERF_VERSION')
    technology = kwargs.get('TECHNOLOGY')
    carrier_bw = kwargs.get('CARRIER_BW')
    mimo = kwargs.get('MIMO')
    modulation = kwargs.get('MODULATION')
    LTE_bitrate = kwargs.get('LTE_BITRATE')
    runtime = kwargs.get('RUNTIME')
    t_idle_bw_profile = kwargs.get('T_IDLE_BW_PROFILE')
    t_idle_bw_seq = kwargs.get('T_IDLE_BW_SEQ')
    profile_running_time = kwargs.get('PROFILE_RUNNING_TIME')
    profile_running_seq = kwargs.get('PROFILE_RUNNING_SEQ')
    ue_port = kwargs.get('UE_PORT')
    ue_ip = kwargs.get('UE_IP')

    # print(ue_ip) # 多UE


    # import pprint
    # pprint.pprint(kwargs)


    if os.getenv('DEBUGGING', '0') == '1':
        runtime = 1  # hours
        t_idle_bw_profile = 0.2  # default 3 minutes
        t_idle_bw_seq = 0.4  # default 5 minutes
        profile_running_time = {'profile_50': 1,
                                'profile_30': 1,
                                'profile_10': 1,
                                'profile_70': 1,
                                'profile_100': 1,
                                'extreme_70': 1,
                                'extreme_50': 1,
                                'short_traffic': 1,
                                'resource_70': 1,
                                'resource_50': 1}

    if 'NSA' not in technology:
        LTE_bitrate = 0
    bw_rate = get_bandwidth_rate(technology, carrier_bw, mimo, modulation, LTE_bitrate)
    # print("bw_rate: ",bw_rate)
    if bw_rate == 'ERROR':
        gLogger.error('Iperf bandwidth rate not available')
        exit(0)

    iperf_tput_log = radio + '_' + technology + '_' + carrier_bw + '_iperf_tput' + test_date + '.log'

    # logger
    gLogger.info("----------------------------------------------------")
    gLogger.info("Test information - Technology:  %s" % technology)
    gLogger.info("Test information - Carrier BW:  %s" % carrier_bw)
    gLogger.info("Test information - MIMO config: %s" % mimo)
    gLogger.info("Test information - Modulation:  %s" % modulation)
    gLogger.info("Test information - Server IP:   %s" % SERVER_IP)
    gLogger.info("Test information - UE\'s IP:    %s" % ue_ip)
    gLogger.info("Test information - Test date:   %s" % (datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S")))
    gLogger.info("----------------------------------------------------\n")

    gLogger.info("Traffic Test Information:")
    gLogger.info("Total runtime: %d hours" % runtime)
    gLogger.info("The Traffic is run in the following sequence:")
    for i in range(len(profile_running_seq)):
        profile = profile_running_seq[i]
        t_running = profile_running_time[profile]
        gLogger.info("Profile:  %15s : %d minutes" % (profile, t_running))
    gLogger.info("----------------------------------------------------\n")

    time.sleep(1)
    show_remaining_time(5)

    t_elapsed = 0
    seq_index = 0
    start_time = time.time()
    while t_elapsed < runtime * 60 * 60:
        profile = profile_running_seq[seq_index]
        seq_index = seq_index + 1
        t_running = profile_running_time[profile]
        t_idle = t_idle_bw_profile

        if seq_index == len(profile_running_seq):
            seq_index = 0
            t_idle = t_idle_bw_seq

        if t_running > 0:
            if profile == "profile_idle":
                gLogger.info("START RUNNING PROFILE: %s" % profile)
                show_remaining_time(t_running * 60)
            else:
                gLogger.info("START RUNNING PROFILE: %s" % profile)

                run_traffic_model(profile, t_running, SERVER_IP, ue_port, bw_rate, iperf_tput_log, iperf_version, ue_ip,
                                  queue)

                gLogger.info("COMPLETE RUNNING PROFILE: %s" % profile)
                gLogger.info("Please wait for running the next profile: %s" % profile_running_seq[seq_index])
                show_remaining_time(t_idle * 60)
        t_elapsed = time.time() - start_time

    elapsed_hours, elapsed_minutes, elapsed_seconds = get_elapsed_time(start_time)
    gLogger.info("==========================\nCompletion of the test at %s" % (
        datetime.datetime.now().strftime("%d%b%Y_%H:%M:%S")))
    gLogger.info("Total Elapsed Time:   %dH : %dM : %dS\n" % (elapsed_hours, elapsed_minutes, elapsed_seconds))


# if __name__ == "__main__":
#     pass
