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
from honeybadgerbft.core.honeybadger import HoneyBadgerBFT
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


### Test asynchronous common subset
def test_honeybadger(N=4, f=1, seed=None):
    setup_logging()
    logger = getLogger(LOGGER_NAME)

    sid = 'sidA'
    # Generate threshold sig keys
    sPK, sSKs = dealer(N, f+1, seed=seed)
    # Generate threshold enc keys
    ePK, eSKs = tpke.dealer(N, f+1)

    rnd = random.Random(seed)
    #print 'SEED:', seed
    router_seed = rnd.random()
    sends, recvs = simple_router(N, seed=router_seed)

    badgers = [None] * N
    threads = [None] * N
    for i in range(N):
        badgers[i] = HoneyBadgerBFT(sid, i, 1, N, f,
                                    sPK, sSKs[i], ePK, eSKs[i],
                                    sends[i], recvs[i])
        threads[i] = gevent.spawn(badgers[i].run)

    time_at_start = datetime.now().timestamp()
    logger.info(f"Time at start: {time_at_start}")

    for i in range(N):
        #if i == 1: continue
        badgers[i].submit_tx('<[HBBFT Input {}]>'.format(i)*100000)
    logger.debug("Done submitting big input")
    for i in range(N):
        badgers[i].submit_tx('<[HBBFT Input %d]>' % (i+10))

    for i in range(N):
        badgers[i].submit_tx('<[HBBFT Input %d]>' % (i+20))

    #gevent.killall(threads[N-f:])
    #gevent.sleep(3)
    #for i in range(N-f, N):
    #    inputs[i].put(0)
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

