import random

import gevent
from gevent import Greenlet
from gevent.queue import Queue
from pytest import mark, raises
from datetime import datetime


from honeybadgerbft.core.vaba import vaba
from honeybadgerbft.core.leaderelection import leader_election


### RBC
from honeybadgerbft.crypto.threshsig.boldyreva import dealer

def simple_router(N, maxdelay=0.01, seed=None):
    """Builds a set of connected channels, with random delay
    @return (receives, sends)
    """
    rnd = random.Random(seed)
    #if seed is not None: print 'ROUTER SEED: %f' % (seed,)

    queues = [Queue() for _ in range(N)]

    def makeSend(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            #print 'SEND %8s [%2d -> %2d] %.2f' % (o[0], i, j, delay)
            gevent.spawn_later(delay, queues[j].put, (i,o))
            #queues[j].put((i, o))
        return _send

    def makeBroadcast(i):
        def _send(j, o):
            delay = rnd.random() * maxdelay
            #print 'SEND %8s [%2d -> %2d] %.2f' % (o[0], i, j, delay)
            gevent.spawn_later(delay, queues[j].put, (i,o))
            #queues[j].put((i, o))

        def _bc(o):
            for j in range(N):
                _send(j,o)
        return _bc

    def makeRecv(j):
        def _recv():
            (i,o) = queues[j].get()
            #print 'RECV %8s [%2d -> %2d]' % (o[0], i, j)
            return (i,o)
        return _recv

    return ([makeSend(i) for i in range(N)],
            [makeBroadcast(k) for k in range(N)],
            [makeRecv(j) for j in range(N)])


# def byzantine_router(N, maxdelay=0.01, seed=None, **byzargs):
#     """Builds a set of connected channels, with random delay,
#     and possibly byzantine behavior.
#     """
#     rnd = random.Random(seed)
#     queues = [Queue() for _ in range(N)]
#
#     def makeSend(i):
#         def _send(j, o):
#             delay = rnd.random() * maxdelay
#             if i == byzargs.get('byznode'):
#                 if o[0] == byzargs.get('message_type'):
#                     screwed_up = list(o)
#                     if o[0] in ('VAL', 'ECHO'):
#                         screwed_up[3] = 'screw it'
#                     o = tuple(screwed_up)
#             if byzargs.get('invalid_message_type'):
#                 byz_o = list(o)
#                 byz_o[0] = byzargs.get('invalid_message_type')
#                 o = tuple(byz_o)
#             if (byzargs.get('fake_sender') and
#                     o[0] == 'VAL' and i == byzargs.get('byznode')):
#                 gevent.spawn_later(delay, queues[j].put, ((i + 1) % 4, o))
#             elif byzargs.get('slow_echo') and i != 2:
#                 if o[0] == 'READY':
#                     gevent.spawn_later(delay*0.001, queues[j].put, (i, o))
#                 elif o[0] == 'ECHO':
#                     gevent.spawn_later(delay*10, queues[j].put, (i, o))
#                 else:
#                     gevent.spawn_later(delay, queues[j].put, (i, o))
#             else:
#                 gevent.spawn_later(delay, queues[j].put, (i, o))
#             if byzargs.get('redundant_message_type') == o[0]:
#                 gevent.spawn_later(delay, queues[j].put, (i, o))
#
#         return _send
#
#     def makeRecv(j):
#         def _recv():
#             i, o = queues[j].get()
#             return i ,o
#         return _recv
#
#     return ([makeSend(i) for i in range(N)],
#             [makeRecv(j) for j in range(N)])

def _make_election(N=4, f=1, seed=None):
    # Generate keys
    PK, SKs = dealer(N, f+1, random.seed(datetime.now()))
    sid = 'sidA'
    rnd = random.Random(seed)
    router_seed = rnd.random()
    _, sends, recvs = simple_router(N, seed=seed)
    return [leader_election(sid, i, N, f, PK, SKs[i], sends[i], recvs[i]) for i in range(N)]



def _test_vaba(N=4, f=1, leader=None, seed=None):
    # Crash up to f nodes
    #if seed is not None: print 'SEED:', seed
    sid = 'sidA'
    rnd = random.Random(seed)
    router_seed = rnd.random()
    if leader is None: leader = rnd.randint(0,N-1)
    sends, broadcasts, recvs = simple_router(N, seed=router_seed)
    threads = []
    PK, SKs = dealer(N, 2 * f + 1, random.seed())

    inputs = [Queue(1) for _ in range(N)]
    m = b"Hello!VABA"

    elections = _make_election()

    def ex_ba_validation():
        return True

    for i in range(N):
        input = inputs[i].get
        t = Greenlet(vaba, sid, i, N, f, input, recvs[i], sends[i], broadcasts[i], PK, SKs[i], ex_ba_validation, elections[i])
        t.start()
        threads.append(t)
        inputs[i].put_nowait(m)
        gevent.sleep(0)     # Let the leader get out its first message

    # Crash f of the nodes
    crashed = set()
    # print 'Leader:', leader
    # for _ in range(f):
    #     i = rnd.choice(range(N))
    #     crashed.add(i)
    #     threads[i].kill()
    #     threads[i].join()
    # print 'Crashed:', crashed
    gevent.joinall(threads)
    for i,t in enumerate(threads):
        if i not in crashed: assert t.value == m
    # assert len(set([t.value for t in threads])) == 1


# @mark.parametrize('seed', range(20))
# @mark.parametrize('N,f', ((4, 1), (5, 1), (8, 2)))
@mark.parametrize('seed', range(1))
@mark.parametrize('N,f', [(4, 1)])
def test_pbbroadcast_s4(N, f, seed):
    _test_vaba(N=N, f=f, seed=seed)
#
#
# @mark.parametrize('seed', range(20))
# @mark.parametrize('tag', ('VAL', 'ECHO'))
# @mark.parametrize('N,f', ((4, 1), (5, 1), (8, 2)))
# def test_rbc_when_merkle_verify_fails(N, f, tag, seed):
#     rnd = random.Random(seed)
#     leader = rnd.randint(0, N-1)
#     byznode = 1
#     sends, recvs = byzantine_router(
#         N, seed=seed, byznode=byznode, message_type=tag)
#     threads = []
#     leader_input = Queue(1)
#     for pid in range(N):
#         sid = 'sid{}'.format(leader)
#         input = leader_input.get if pid == leader else None
#         t = Greenlet(reliablebroadcast, sid, pid, N, f, leader, input, recvs[pid], sends[pid])
#         t.start()
#         threads.append(t)
#
#     m = b"Hello! This is a test message."
#     leader_input.put(m)
#     completed_greenlets = gevent.joinall(threads, timeout=0.5)
#     expected_rbc_result = None if leader == byznode and tag == 'VAL' else m
#     assert all([t.value == expected_rbc_result for t in threads])
#
#
# @mark.parametrize('seed', range(3))
# @mark.parametrize('N,f', ((4, 1), (5, 1), (8, 2)))
# def test_rbc_receives_val_from_sender_not_leader(N, f, seed):
#     rnd = random.Random(seed)
#     leader = rnd.randint(0, N-1)
#     sends, recvs = byzantine_router(
#         N, seed=seed, fake_sender=True, byznode=leader)
#     threads = []
#     leader_input = Queue(1)
#     for pid in range(N):
#         sid = 'sid{}'.format(leader)
#         input = leader_input.get if pid == leader else None
#         t = Greenlet(reliablebroadcast, sid, pid, N, f, leader, input, recvs[pid], sends[pid])
#         t.start()
#         threads.append(t)
#
#     m = "Hello! This is a test message."
#     leader_input.put(m)
#     completed_greenlets = gevent.joinall(threads, timeout=0.5)
#     expected_rbc_result = None
#     assert all([t.value == expected_rbc_result for t in threads])
#
#
# @mark.parametrize('seed', range(2))
# @mark.parametrize('tag', ('ECHO', 'READY'))
# @mark.parametrize('N,f', ((4, 1),))
# def test_rbc_with_redundant_message(N, f, tag, seed):
#     rnd = random.Random(seed)
#     leader = rnd.randint(0, N-1)
#     sends, recvs = byzantine_router(N, seed=seed, redundant_message_type=tag)
#     threads = []
#     leader_input = Queue(1)
#     for pid in range(N):
#         sid = 'sid{}'.format(leader)
#         input = leader_input.get if pid == leader else None
#         t = Greenlet(reliablebroadcast, sid, pid, N, f,
#                      leader, input, recvs[pid], sends[pid])
#         t.start()
#         threads.append(t)
#
#     m = b"Hello! This is a test message."
#     leader_input.put(m)
#     completed_greenlets = gevent.joinall(threads, timeout=0.5)
#     expected_rbc_result = m
#     assert all([t.value == expected_rbc_result for t in threads])
#
#
# @mark.parametrize('seed', range(1))
# @mark.parametrize('N,f', ((4, 1),))
# def test_rbc_decode_in_echo_handling_step(N, f, seed):
#     """The goal of this test is to simply force the decode operation
#     to take place upon rception of an ECHO message, (when other
#     necessary conditions are met), as opposed to the operation taking
#     place upon reception of a READY message.
#
#     The test is perhaps hackish at best, but nevertheless does achieve
#     its intent.
#
#     The test slows down the broadcasting of ECHO messages, meanwhile
#     speeding up the broadcasting of READY messages.
#     """
#     rnd = random.Random(seed)
#     leader = rnd.randint(0, N-1)
#     sends, recvs = byzantine_router(N, seed=seed, slow_echo=True)
#     threads = []
#     leader_input = Queue(1)
#     for pid in range(N):
#         sid = 'sid{}'.format(leader)
#         input = leader_input.get if pid == leader else None
#         t = Greenlet(reliablebroadcast, sid, pid, N, f,
#                      leader, input, recvs[pid], sends[pid])
#         t.start()
#         threads.append(t)
#
#     m = b"Hello! This is a test message."
#     leader_input.put(m)
#     completed_greenlets = gevent.joinall(threads, timeout=1)
#     expected_rbc_result = m
#     assert all([t.value == expected_rbc_result for t in threads])
#
#
# @mark.parametrize('seed', range(2))
# @mark.parametrize('tag', ('CHECKTHISOUT!', 'LETSGO!'))
# @mark.parametrize('N,f', ((4, 1),))
# def test_rbc_with_invalid_message(N, f, tag, seed):
#     rnd = random.Random(seed)
#     leader = rnd.randint(0, N-1)
#     sends, recvs = byzantine_router(N, seed=seed, invalid_message_type=tag)
#     threads = []
#     leader_input = Queue(1)
#     for pid in range(N):
#         sid = 'sid{}'.format(leader)
#         input = leader_input.get if pid == leader else None
#         t = Greenlet(reliablebroadcast, sid, pid, N, f,
#                      leader, input, recvs[pid], sends[pid])
#         t.start()
#         threads.append(t)
#
#     m = "Hello! This is a test message."
#     leader_input.put(m)
#     completed_greenlets = gevent.joinall(threads, timeout=0.5)
#     expected_rbc_result = None
#     assert all([t.value == expected_rbc_result for t in threads])


# TODO: Test more edge cases, like Byzantine behavior
