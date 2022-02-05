import os
import logging
from our_srcs.consts import *
import datetime

def setup_logging():
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)


    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('(%(asctime)s) %(levelname)s: %(message)s', datefmt='%H:%M:%S')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    cur_time = datetime.datetime.now()
    fi = logging.FileHandler(LOG_PATH.format(cur_time.year, cur_time.month, cur_time.day, cur_time.hour,
                                             cur_time.minute, cur_time.second))
    fi.setLevel(logging.DEBUG)
    fi.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fi)



