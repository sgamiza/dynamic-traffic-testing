import logging
import os
import datetime
import sys



def configure_logging():

    script_name = os.path.basename(sys.argv[0])

    iperf_logpath = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(iperf_logpath):
        os.makedirs(iperf_logpath)

    test_date = datetime.datetime.now().strftime('_%m%d%Y_%I%M%S')
    gLogName = f"{script_name}{test_date}.log"
    gLogName = os.path.join(iperf_logpath, gLogName)

    logging.basicConfig(
        filename=gLogName,
        format='%(levelname)s | %(asctime)s | %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.DEBUG
    )

    logFormatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    logger = logging.getLogger()

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logging.getLogger('pyvisa').setLevel(logging.ERROR)
    logging.getLogger('paramiko.transport').setLevel(logging.ERROR)



