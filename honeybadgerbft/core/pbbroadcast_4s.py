import logging
from gevent import Greenlet
from gevent.queue import Queue

logger = logging.getLogger(__name__)


def pbbroadcast_4s(id, pid, N, f, leader, input, receive, send, broadcast, PK, SK):
    S = [{} for _ in range(4)]
    output_queue = Queue(1)
    key = Queue(1)
    lock = Queue(1)
    commit = Queue(1)
    input_value = []
    stop = [False, False, False, False]

    def _recv():
        while True:
            (i, (_, j, cmd, (v, sig_ex, sig_in))) = receive()
            assert i == leader
            assert _ == id
            nonlocal stop

            logger.debug(f'follower received i, _, r, sig: {i, _, j, cmd, v, sig_ex, sig_in}',
                         extra={'nodeid': pid, 'epoch': j})
            if cmd == 'send':
                if stop[j] == False and ex_sbc_validation(_, j, v, sig_ex, sig_in):
                    h = PK.hash_message(str((id, j, v)))
                    stop[j] = True
                    if j == 1:
                        key.put_nowait((id, (v, sig_in)))
                    elif j == 2:
                        lock.put_nowait((id, (v, sig_in)))
                    elif j == 3:
                        commit.put_nowait((id, (v, sig_in)))
                        output_queue.put_nowait(v)
                    logger.debug(f'follower acked i, id, ack, sig: {i, id, j, "ack", SK.sign(h)}',
                                 extra={'nodeid': pid, 'epoch': j})
                    send(leader, (id, j, 'ack', SK.sign(h)))


            else:
                assert cmd == 'abandon'
                stop[j] = True

    def ex_sbc_validation(id, j, v, sig_ex, sig_in):
        if j == 0 and ex_bc_validation(id, v, sig_ex):
            return True
        if j > 0 and threshold_validate(id, j - 1, v, sig_in):
            return True
        return False

    def ex_bc_validation(id, v, sig_ex):
        # TODO: add external validation logic
        return True

    def threshold_validate(id, j, v, sig_in):
        h = PK.hash_message(str((id, j, v)))
        try:
            PK.verify_signature(sig_in, h)
            return True
        except AssertionError:
            print("threshold_validate failure!")
            return False

    def _leader_recv():
        while True:
            (i, (_, j, cmd, v)) = receive()

            assert _ == id
            if cmd == 'send':
                logger.debug(f'leader received i, _, r, sig: {i, _, j, cmd, v}',
                             extra={'nodeid': pid, 'epoch': j})
                h = PK.hash_message(str((id, j, v[0])))
                send(leader, (id, j, 'ack', SK.sign(h)))
                continue

            # if message command is ack
            (i, (_, j, ack, sig_share)) = (i, (_, j, cmd, v))
            # logger.debug(f'leader received i, _, r, sig: {i, _, j, ack, sig_share}',
            #              extra={'nodeid': pid, 'epoch': j})
            assert ack == 'ack'
            h = PK.hash_message(str((id, j, input_value[0])))
            try:
                PK.verify_share(sig_share, i, h)
                print("Signature share succeeded!", (id, pid, i, j, input_value[0]))
            except AssertionError:
                print("Signature share failed!", (id, pid, i, j, input_value[0]))
                continue
            S[j][i] = sig_share

            if len(S[j]) == 2 * f + 1:
                sigs = dict(list(S[j].items())[:2 * f + 1])
                sig = PK.combine_shares(sigs)
                assert PK.verify_signature(sig, h)
                logger.debug(f'put sig {sig} in output queue',
                             extra={'nodeid': pid, 'epoch': j})
                output_queue.put_nowait(sig)

    if leader == pid:
        v = input()
        sig_ex = None
        sig_in = None
        input_value.append(v)
        Greenlet(_leader_recv).start()
        for j in range(4):
            print("round %d broadcast start\n" % (j))
            broadcast((id, j, 'send', (v, sig_ex, sig_in)))
            sig_in = output_queue.get()
        return sig_in

    else:
        Greenlet(_recv).start()

    return output_queue.get()
