import random

import gevent
from gevent.queue import Queue
from pytest import mark


@mark.demo
def test_issue59_attack_demo(mocker, monkeypatch):
    from .byzantine import byz_ba_issue_59, broadcast_router
    from .test_binaryagreement import _make_coins
    from honeybadgerbft.core import binaryagreement

    def mocked_conf_message_receiver(**kwargs):
        pass

    def mocked_conf_phase_handler(**kwargs):
        return kwargs['values']

    monkeypatch.setattr(
        binaryagreement, 'handle_conf_messages', mocked_conf_message_receiver)
    monkeypatch.setattr(
        binaryagreement, 'wait_for_conf_values', mocked_conf_phase_handler)

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

    byz_thread = gevent.spawn(byz_ba_issue_59, sid, 3, N, f, coins[3],
                              inputs[3].get, outputs[3].put_nowait, sends[3], recvs[3])
    threads.append(byz_thread)

    for i in (2, 0, 1):
        t = gevent.spawn(binaryagreement.binaryagreement, sid, i, N, f, coins[i],
                         inputs[i].get, outputs[i].put_nowait, sends[i], recvs[i])
        threads.append(t)

    inputs[0].put(0)    # A_0
    inputs[1].put(0)    # A_1
    inputs[2].put(1)    # B
    inputs[3].put(0)    # F (x)

    for i in range(N):
        outputs[i].get()
