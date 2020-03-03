import logging
from gevent import Greenlet
from gevent.queue import Queue

logger = logging.getLogger(__name__)


def pbbroadcast(id, j, pid, N, f, leader, input, receive, send, broadcast, PK, SK):
    S = {}
    output_queue = Queue(1)
    input_value = []
    stop = False

    def _recv():
        (i, (_, cmd, v)) = receive()
        assert i == leader
        nonlocal stop

        logger.debug(f'follower received i, _, r, sig: {i, _, cmd, v}',
                     extra={'nodeid': pid, 'epoch': j})
        if cmd == 'send':
            if stop == False:
                h = PK.hash_message(str((id, v)))
                stop = True
                output_queue.put_nowait(v)
                # logger.debug(f'follower acked i, id, ack, sig: {i, id, "ack", SK.sign(h)}',
                #              extra={'nodeid': pid, 'epoch': j})
                send(leader, (id, 'ack', SK.sign(h)))


        else:
            assert cmd == 'abandon'
            stop = True

    def _leader_recv():
        while True:
            (i, (_, cmd, v)) = receive()
            if cmd == 'send':
                h = PK.hash_message(str((id, v)))
                send(leader, (id, 'ack', SK.sign(h)))
                continue
            (i, (_, ack, sig_share)) = (i, (_, cmd, v))
            logger.debug(f'leader received i, _, r, sig: {i, _, ack, sig_share}',
                         extra={'nodeid': pid, 'epoch': j})
            assert ack == 'ack'
            h = PK.hash_message(str((id, input_value[0])))
            try:
                PK.verify_share(sig_share, i, h)
            except AssertionError:
                print("Signature share failed!", (id, pid, i, j))
                continue
            S[i] = sig_share

            if len(S) == 2 * f + 1:
                sigs = dict(list(S.items())[:2 * f + 1])
                sig = PK.combine_shares(sigs)
                assert PK.verify_signature(sig, h)
                logger.debug(f'put sig {sig} in output queue',
                             extra={'nodeid': pid, 'epoch': j})
                output_queue.put_nowait(sig)

    if leader == pid:
        # Todo: add signature value
        v = input()
        input_value.append(v)
        Greenlet(_leader_recv).start()
        broadcast((id, 'send', v))

    else:
        Greenlet(_recv).start()

    return output_queue.get()
