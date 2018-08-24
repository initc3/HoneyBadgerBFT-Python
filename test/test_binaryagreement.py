import logging
import unittest
import gevent
import random

from gevent.event import Event
from gevent.queue import Queue
from honeybadgerbft.core.commoncoin import shared_coin
from honeybadgerbft.core.binaryagreement import binaryagreement
from honeybadgerbft.crypto.threshsig.boldyreva import dealer
from collections import defaultdict

from pytest import mark, raises

logger = logging.getLogger(__name__)

def simple_broadcast_router(N, maxdelay=0.005, seed=None):
    """Builds a set of connected channels, with random delay
    @return (receives, sends)
    """
    rnd = random.Random(seed)
    #if seed is not None: print 'ROUTER SEED: %f' % (seed,)
    
    queues = [Queue() for _ in range(N)]
    _threads = []

    def makeBroadcast(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            #print 'SEND   %8s [%2d -> %2d] %2.1f' % (o[0], i, j, delay*1000), o[1:]
            gevent.spawn_later(delay, queues[j].put, (i,o))
            #queues[j].put((i, o))
        def _bc(o):
            #print 'BCAST  %8s [%2d ->  *]' % (o[0], i), o[1]
            for j in range(N): _send(j, o)
        return _bc

    def makeRecv(j):
        def _recv():
            (i,o) = queues[j].get()
            #print 'RECV %8s [%2d -> %2d]' % (o[0], i, j)
            return (i,o)
        return _recv
        
    return ([makeBroadcast(i) for i in range(N)],
            [makeRecv(j)      for j in range(N)])


def byzantine_broadcast_router(N, maxdelay=0.005, seed=None, **byzargs):
    """Builds a set of connected channels, with random delay.

    :return: (receives, sends) endpoints.
    """
    rnd = random.Random(seed)
    queues = [Queue() for _ in range(N)]
    _threads = []

    def makeBroadcast(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            if j == byzargs.get('byznode'):
                try:
                    byz_tag = byzargs['byz_message_type']
                except KeyError:
                    pass
                else:
                    o = list(o)
                    o[0] = byz_tag
                    o = tuple(o)

            gevent.spawn_later(delay, queues[j].put, (i, o))

            if (j == byzargs.get('byznode') and
                    o[0] == byzargs.get('redundant_msg_type')):
                gevent.spawn_later(delay, queues[j].put, (i, o))

        def _bc(o):
            for j in range(N):
                _send(j, o)

        return _bc

    def makeRecv(j):
        def _recv():
            (i,o) = queues[j].get()
            return (i,o)

        return _recv

    return ([makeBroadcast(i) for i in range(N)],
            [makeRecv(j) for j in range(N)])


def release_held_messages(q, receivers):
    for m in q:
        receivers[m['receiver']].put((m['sender'], m['msg']))


def dummy_coin(sid, N, f):
    counter = defaultdict(int)
    events = defaultdict(Event)
    def getCoin(round):
        # Return a pseudorandom number depending on the round, without blocking
        counter[round] += 1
        if counter[round] == f+1: events[round].set()
        events[round].wait()
        return hash((sid,round)) % 2
    return getCoin


### Test binary agreement with a dummy coin
def _test_binaryagreement_dummy(N=4, f=1, seed=None):
    # Generate keys
    sid = 'sidA'    
    # Test everything when runs are OK
    #if seed is not None: print 'SEED:', seed
    rnd = random.Random(seed)
    router_seed = rnd.random()
    sends, recvs = simple_broadcast_router(N, seed=seed)

    threads = []
    inputs = []
    outputs = []
    coin = dummy_coin(sid, N, f)  # One dummy coin function for all nodes

    for i in range(N):
        inputs.append(Queue())
        outputs.append(Queue())
        
        t = gevent.spawn(binaryagreement, sid, i, N, f, coin,
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    for i in range(N):
        inputs[i].put(random.randint(0,1))
    #gevent.killall(threads[N-f:])
    #gevent.sleep(3)
    #for i in range(N-f, N):
    #    inputs[i].put(0)
    try:
        outs = [outputs[i].get() for i in range(N)]
        assert len(set(outs)) == 1
        try: gevent.joinall(threads)
        except gevent.hub.LoopExit: pass
    except KeyboardInterrupt:
        gevent.killall(threads)
        raise


def test_binaryagreement_dummy():
    _test_binaryagreement_dummy()


@mark.parametrize('msg_type', ('EST', 'AUX', 'CONF'))
@mark.parametrize('byznode', (1, 2, 3))
def test_binaryagreement_dummy_with_redundant_messages(byznode, msg_type):
    N = 4
    f = 1
    seed = None
    sid = 'sidA'
    rnd = random.Random(seed)
    router_seed = rnd.random()
    sends, recvs = byzantine_broadcast_router(
        N, seed=seed, byznode=byznode, redundant_msg_type=msg_type)
    threads = []
    inputs = []
    outputs = []
    coin = dummy_coin(sid, N, f)  # One dummy coin function for all nodes

    for i in range(N):
        inputs.append(Queue())
        outputs.append(Queue())
        t = gevent.spawn(binaryagreement, sid, i, N, f, coin,
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    for i in range(N):
        inputs[i].put(random.randint(0,1))

    outs = [outputs[i].get() for i in range(N) if i != byznode]
    assert all(v in (0, 1) and v == outs[0] for v in outs)

    try:
        gevent.joinall(threads)
    except gevent.hub.LoopExit:
        pass


@mark.parametrize('byznode', (1, 2, 3))
def test_binaryagreement_dummy_with_byz_message_type(byznode):
    N = 4
    f = 1
    seed = None
    sid = 'sidA'
    rnd = random.Random(seed)
    router_seed = rnd.random()
    sends, recvs = byzantine_broadcast_router(
        N, seed=seed, byznode=byznode, byz_message_type='BUG')
    threads = []
    inputs = []
    outputs = []
    coin = dummy_coin(sid, N, f)  # One dummy coin function for all nodes

    for i in range(N):
        inputs.append(Queue())
        outputs.append(Queue())
        t = gevent.spawn(binaryagreement, sid, i, N, f, coin,
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    for i in range(N):
        inputs[i].put(random.randint(0,1))

    outs = [outputs[i].get() for i in range(N) if i != byznode]
    assert all(v in (0, 1) and v == outs[0] for v in outs)

    try:
        gevent.joinall(threads)
    except gevent.hub.LoopExit:
        pass


### Test binary agreement with boldyreva coin
def _make_coins(sid, N, f, seed):
    # Generate keys
    PK, SKs = dealer(N, f+1)
    rnd = random.Random(seed)
    router_seed = rnd.random()
    sends, recvs = simple_broadcast_router(N, seed=seed)
    coins = [shared_coin(sid, i, N, f, PK, SKs[i], sends[i], recvs[i]) for i in range(N)]
    return coins

def _test_binaryagreement(N=4, f=1, seed=None):
    # Generate keys
    sid = 'sidA'
    # Test everything when runs are OK
    #if seed is not None: print 'SEED:', seed
    rnd = random.Random(seed)

    # Instantiate the common coin
    coins_seed = rnd.random()
    coins = _make_coins(sid+'COIN', N, f, coins_seed)

    # Router
    router_seed = rnd.random()
    sends, recvs = simple_broadcast_router(N, seed=seed)

    threads = []
    inputs = []
    outputs = []

    for i in range(N):
        inputs.append(Queue())
        outputs.append(Queue())
        
        t = gevent.spawn(binaryagreement, sid, i, N, f, coins[i],
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    for i in range(N):
        inputs[i].put(random.randint(0,1))
    #gevent.killall(threads[N-f:])
    #gevent.sleep(3)
    #for i in range(N-f, N):
    #    inputs[i].put(0)
    try:
        outs = [outputs[i].get() for i in range(N)]
        assert len(set(outs)) == 1
        try: gevent.joinall(threads)
        except gevent.hub.LoopExit: pass
    except KeyboardInterrupt:
        gevent.killall(threads)
        raise

def test_binaryagreement():
    for i in range(5): _test_binaryagreement(seed=i)


@mark.parametrize('values,s,already_decided,expected_est,'
                  'expected_already_decided,expected_output', (
    ({0}, 0, None, 0, 0, 0),
    ({1}, 1, None, 1, 1, 1),
))
def test_set_next_round_estimate_with_decision(values, s, already_decided,
                    expected_est, expected_already_decided, expected_output):
    from honeybadgerbft.core.binaryagreement import set_new_estimate
    decide = Queue()
    updated_est, updated_already_decided = set_new_estimate(
        values=values,
        s=s,
        already_decided=already_decided,
        decide=decide.put,
    )
    assert updated_est == expected_est
    assert updated_already_decided == expected_already_decided
    assert decide.get() == expected_output


@mark.parametrize('values,s,already_decided,'
                  'expected_est,expected_already_decided', (
    ({0}, 0, 1, 0, 1),
    ({0}, 1, None, 0, None),
    ({0}, 1, 0, 0, 0),
    ({0}, 1, 1, 0, 1),
    ({1}, 0, None, 1, None),
    ({1}, 0, 0, 1, 0),
    ({1}, 0, 1, 1, 1),
    ({1}, 1, 0, 1, 0),
    ({0, 1}, 0, None, 0, None),
    ({0, 1}, 0, 0, 0, 0),
    ({0, 1}, 0, 1, 0, 1),
    ({0, 1}, 1, None, 1, None),
    ({0, 1}, 1, 0, 1, 0),
    ({0, 1}, 1, 1, 1, 1),
))
def test_set_next_round_estimate(values, s, already_decided,
                                 expected_est, expected_already_decided):
    from honeybadgerbft.core.binaryagreement import set_new_estimate
    decide = Queue()
    updated_est, updated_already_decided = set_new_estimate(
        values=values,
        s=s,
        already_decided=already_decided,
        decide=decide.put,
    )
    assert updated_est == expected_est
    assert updated_already_decided == expected_already_decided
    assert decide.empty()


@mark.parametrize('values,s,already_decided', (
    ({0}, 0, 0),
    ({1}, 1, 1),
))
def test_set_next_round_estimate_raises(values, s, already_decided):
    from honeybadgerbft.core.binaryagreement import set_new_estimate
    from honeybadgerbft.exceptions import AbandonedNodeError
    with raises(AbandonedNodeError):
        updated_est, updated_already_decided = set_new_estimate(
            values=values,
            s=s,
            already_decided=already_decided,
            decide=None,
        )


def test_issue59_attack(caplog):
    from .byzantine import byz_ba_issue_59, broadcast_router
    N = 4
    f = 1
    seed = None
    sid = 'sidA'
    rnd = random.Random(seed)
    sends, recvs = broadcast_router(N)
    threads = []
    inputs = []
    outputs = []

    coins_seed = rnd.random()
    coins = _make_coins(sid+'COIN', N, f, coins_seed)

    for i in range(4):
        inputs.append(Queue())
        outputs.append(Queue())

    t = gevent.spawn(byz_ba_issue_59, sid, 3, N, f, coins[3],
                     inputs[3].get, outputs[3].put_nowait, sends[3], recvs[3])
    threads.append(t)

    for i in (2, 0, 1):
        t = gevent.spawn(binaryagreement, sid, i, N, f, coins[i],
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    inputs[0].put(0)    # A_0
    inputs[1].put(0)    # A_1
    inputs[2].put(1)    # B
    inputs[3].put(0)    # F (x)

    try:
        outs = [outputs[i].get() for i in range(N)]
    except gevent.hub.LoopExit:
        ba_node_2_log_records = [
            record for record in caplog.records
            if record.nodeid == 2 and record.module == 'binaryagreement'
        ]
        round_0_records = [
            record for record in ba_node_2_log_records if record.epoch == 0
        ]
        round_1_records = [
            record for record in ba_node_2_log_records if record.epoch == 1
        ]
        conf_phase_record = [
            record for record in round_0_records
            if record.message == 'Completed CONF phase with values = {0, 1}'
        ]
        assert len(conf_phase_record) == 1
        coin_value_record = [
            record for record in round_0_records
            if record.message.startswith('Received coin with value = ')
        ]
        assert len(coin_value_record) == 1
        coin_value = coin_value_record[0].message.split('=')[1]
        round_1_begin_log = [
            record for record in round_1_records
            if record.message.startswith('Starting with est = ')
        ]
        assert len(round_1_begin_log) == 1
        est_value_round_1 = round_1_begin_log[0].message.split('=')[1]
        assert est_value_round_1 == coin_value

    try:
        gevent.joinall(threads)
    except gevent.hub.LoopExit:
        pass
