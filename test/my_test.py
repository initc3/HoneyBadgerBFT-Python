import random
from collections import defaultdict
import math
from datetime import datetime

import gevent
from gevent.event import Event
from gevent.queue import Queue
from pytest import fixture, mark, raises

import honeybadgerbft.core.honeybadger
#reload(honeybadgerbft.core.honeybadger)
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT, ImprovedHoneyBadgerBFT
from honeybadgerbft.crypto.threshsig.boldyreva import dealer
from honeybadgerbft.crypto.threshenc import tpke
from honeybadgerbft.core.honeybadger import BroadcastTag
from logging import getLogger
from our_srcs.utils import setup_logging
from our_srcs.consts import *

@fixture
def recv_queues(request):
    from honeybadgerbft.core.honeybadger import BroadcastReceiverQueues
    number_of_nodes = getattr(request, 'N', 4)
    queues = {
        tag.value: [Queue() for _ in range(number_of_nodes)]
        for tag in BroadcastTag if tag != BroadcastTag.TPKE
    }
    queues[BroadcastTag.TPKE.value] = Queue()
    return BroadcastReceiverQueues(**queues)



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
            delay *= math.log(len(o)) * 7.5
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


def test_main():
    setup_logging()
    logger = getLogger(LOGGER_NAME)
    _test_num_of_nodes()
    #_test_num_of_identical_inputs()
    #_test_input_sizes()


def _test_num_of_nodes():
    logger = getLogger(LOGGER_NAME)
    logger.info("Testing Number of Nodes")
    for num_of_nodes in NUM_OF_NODE_OPTIONS:
        _test_honeybadgers(num_of_nodes, DEFAULT_NUM_OF_IDENTICAL_INPUTS_OPTIONS, DEFAULT_INPUT_SIZE)

def _test_honeybadgers(num_of_nodes, identical_input, input_size):
    logger = getLogger(LOGGER_NAME)
    logger.info(f"Test Honeybadgers with N={num_of_nodes}, id={identical_input}, size={input_size}")
    for hb_tuple in HONEYBADGERS:
        logger.info("Testing Honeybadger: {}".format(hb_tuple[0]))
        _test_honeybadger_full(hb_tuple[1], num_of_nodes, identical_input, input_size)

### Test asynchronous common subset
def _test_honeybadger_full(HB, N, identical_inputs, input_sizes):
    logger=getLogger(LOGGER_NAME)
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
        badgers[i] = HB(sid, i, 1, N, 1,
                                    sPK, sSKs[i], ePK, eSKs[i],
                                    sends[i], recvs[i])
        threads[i] = gevent.spawn(badgers[i].run)

    time_at_start = datetime.now().timestamp()

    for i in range(N):
        #if i == 1: continue
        badgers[i].submit_tx('<[HBBFT Input {}]>'.format(i))
    for i in range(N):
        badgers[i].submit_tx('<[HBBFT Input %d]>' % (i+10))
    
    for i in range(N):
        badgers[i].submit_tx('<[HBBFT Input %d]>' % (i+20))

    logger.debug("Done submitting all inputs")

    try:
        outs = [threads[i].get() for i in range(N)]

        # Consistency check
        assert len(set(outs)) == 1

        time_at_end = datetime.now().timestamp()
        time_diff = time_at_end - time_at_start
        logger.info(f"Time passed: {time_diff}")

    except KeyboardInterrupt:
        gevent.killall(threads)
        raise

