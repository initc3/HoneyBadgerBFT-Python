import os
import logging
from our_srcs.consts import *
import datetime
import random
import math
from gevent import monkey
monkey.patch_all()
from honeybadgerbft.crypto.threshsig.boldyreva import dealer
from honeybadgerbft.crypto.threshenc import tpke
import gevent
from gevent.event import Event
from gevent.queue import Queue

from our_srcs.consts import *
from logging import getLogger; logger=getLogger(LOGGER_NAME)

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

def setup_honeybadgers(honeybadger_class, N, amount=-1):
    sid = 'sidA'
    # Generate threshold sig keys
    sPK, sSKs = dealer(N, 2, seed=None)
    # Generate threshold enc keys
    ePK, eSKs = tpke.dealer(N, 2)

    rnd = random.Random(None)
    #print 'SEED:', seed
    router_seed = rnd.random()
    sends, recvs = simple_router(N, seed=router_seed)

    badgers = [None] * N
    threads = [None] * N
    for i in range(N):
        badgers[i] = honeybadger_class(sid, i, 1, N, 1,
                                    sPK, sSKs[i], ePK, eSKs[i],
                                    sends[i], recvs[i], amount=amount)
        threads[i] = gevent.spawn(badgers[i].run)
    return badgers, threads

def simple_router(N, maxdelay=0.005, seed=None):
    """Builds a set of connected channels, with random delay

    :return: (receives, sends)
    """
    rnd = random.Random(seed)
    #if seed is not None: print 'ROUTER SEED: %f' % (seed,)

    queues = [Queue() for _ in range(N)]
    _threads = []

    def makeSend(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            messageLen = sum([len(s) if type(s) is str else 0 for s in o[1][2]])
            delay *= math.log(messageLen) if messageLen != 0 else 1
            gevent.spawn_later(delay, queues[j].put_nowait, (i,o))
        return _send

    def makeRecv(j):
        def _recv():
            (i,o) = queues[j].get()
            #print 'RECV %8s [%2d -> %2d]' % (o[0], i, j)
            return (i,o)
        return _recv

    return ([makeSend(i) for i in range(N)],
            [makeRecv(j) for j in range(N)])


