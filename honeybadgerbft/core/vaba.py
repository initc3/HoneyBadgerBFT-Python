import logging

import gevent
from gevent import Greenlet
from gevent.queue import Queue

logger = logging.getLogger(__name__)
UPPERROUNDLIMIT = 3


def vaba(id, pid, N, f, input, receive, send, broadcast, PK, SK, ex_ba_validation, election):
    S = [[{} for _ in range(4)] for _ in range(UPPERROUNDLIMIT)]
    L = [None for _ in range(UPPERROUNDLIMIT)]
    broadcast_sig_queue = Queue(1)
    broadcast_output_queue = Queue(1)
    output = Queue(N)
    view_change_count = [0 for _ in range(UPPERROUNDLIMIT)]
    j = 0
    sig = [(0, None) for _ in range(UPPERROUNDLIMIT)]
    Dkey = [[None] * UPPERROUNDLIMIT for _ in range(N)]
    Dlock = [[None] * UPPERROUNDLIMIT for _ in range(N)]
    Dcommit = [[None] * UPPERROUNDLIMIT for _ in range(N)]
    v = [None for _ in range(UPPERROUNDLIMIT)]
    v[0] = input()
    key = (0,v[0],None)
    lock = 0
    bc_done = [0 for _ in range(UPPERROUNDLIMIT)]
    bc_skip = [{} for _ in range(UPPERROUNDLIMIT)]
    stop = [[[False, False, False, False] for _ in range(UPPERROUNDLIMIT)] for _ in range(N)]
    skip = [False for _ in range(UPPERROUNDLIMIT)]

    def handle_broadcast(m, nodeid):
        ((_id, _pid, _j), rounds, (_v, (_sig_ex, _sig_in))) = m
        assert _j == j
        assert _id == id
        assert _pid == nodeid
        logger.debug(
            f'follower received message "send": id, i ,j, rounds, v, sig_ex, sig_in: {_id, _pid, _j, rounds, _v, _sig_ex, _sig_in}',
            extra={'nodeid': pid, 'epoch': rounds})
        if stop[nodeid][j][rounds] == False and ex_sbc_validation(_id, _pid, _j, rounds, _v, _sig_ex, _sig_in):
            h = PK.hash_message(str(((_id, _pid, _j), rounds, _v)))
            stop[nodeid][j][rounds] = True
            if rounds == 1:
                Dkey[_pid][j] = (_v, _sig_in)
            elif rounds == 2:
                Dlock[_pid][j] = (_v, _sig_in)
            elif rounds == 3:
                Dcommit[_pid][j] = (_v, _sig_in)
            logger.debug(f'follower acked _pid, _id, rounds, ack, sig_share: {_pid, _id, rounds, "ack", SK.sign(h)}',
                         extra={'nodeid': pid, 'epoch': rounds})
            send(nodeid, ('ack', ((_id, _pid, j), rounds, SK.sign(h))))

    def handle_ack(m, nodeid):
        ((_id, _pid, _j), rounds, sig_share) = m
        assert _pid == pid
        logger.debug(f'leader received: {nodeid, "ack", _id, _pid, _j, rounds, sig_share}',
                     extra={'nodeid': pid, 'epoch': rounds})
        h = PK.hash_message(str(((_id, _pid, j), rounds, v[j])))
        if share_validate(sig_share, nodeid, h):
            logger.debug(f'Signature share succeeded! {nodeid, _id, _pid, _j, rounds, sig_share}',
                         extra={'nodeid': pid, 'epoch': rounds})
        else:
            logger.debug(f'Signature share failed! {nodeid, _id, _pid, _j, rounds, sig_share}',
                         extra={'nodeid': pid, 'epoch': rounds})

        S[j][rounds][nodeid] = sig_share

        if len(S[j][rounds]) == 2 * f + 1:
            sigs = dict(list(S[j][rounds].items())[:2 * f + 1])
            sig_combine = PK.combine_shares(sigs)
            assert PK.verify_signature(sig_combine, h)
            logger.debug(f'put sig {sig_combine} in broadcast_sig_queue',
                         extra={'nodeid': pid, 'epoch': rounds})
            broadcast_sig_queue.put_nowait(sig_combine)

    def handle_done(msg, nodeid):
        (_id, _j, (_v, sig_combined)) = msg
        assert _j == j
        logger.debug(f'Received Done Message! {nodeid, _id, _v, sig_combined}',
                     extra={'nodeid': pid, 'epoch': j})
        h = PK.hash_message(str(((_id, nodeid, _j), 3, _v)))
        if threshold_validate(h, sig_combined):
            bc_done[j] += 1
            if bc_done[j] == 2 * f + 1:
                h = PK.hash_message(str((_id, 'skip', j)))
                broadcast(('skip_share', (j, SK.sign(h))))

    def handle_skip_share(msg, nodeid):
        (_j, sig_share) = msg
        h = PK.hash_message(str((id, 'skip', j)))
        assert _j == j
        if share_validate(sig_share, nodeid, h):
            logger.debug(f'Signature share succeeded! {nodeid, id, pid, j, sig_share}',
                         extra={'nodeid': pid, 'epoch': j})
            bc_skip[j][nodeid] = sig_share
            if len(bc_skip[j]) == 2 * f + 1:
                sigs = dict(list(bc_skip[j].items())[:2 * f + 1])
                sig_combine = PK.combine_shares(sigs)
                assert PK.verify_signature(sig_combine, h)
                logger.debug(f'broadcast skip message {id ,"skip", j, sig_combine}',
                             extra={'nodeid': pid, 'epoch': j})
                broadcast(('skip',(id,j,sig_combine)))

    def handle_skip(msg, nodeid):
        (_id, _j, sig_combine) = msg
        assert _id == id
        assert _j == j

        h = PK.hash_message(str((id, 'skip', j)))
        if threshold_validate(h, sig_combine):
            logger.debug(f'Signature share succeeded! {nodeid, id, pid, j, sig_combine}',
                         extra={'nodeid': pid, 'epoch': j})
            if not skip[j]:
                skip[j] = True
                broadcast(('skip', (id, j, sig_combine)))
            else:
                skip[j] = True

    def handle_view_change(msg, nodeid):
        nonlocal key, lock
        (_id, _j, (v2, sig2),(v3, sig3),(v4, sig4)) = msg
        assert _j == j

        view_change_count[j] += 1
        logger.debug(f'View change id, j, v2, v3, v4 {_id, _j, v2, v3, v4}',
                     extra={'nodeid': pid, 'epoch': j})
        if L[j] is None:
            L[j] = election(j)
        if v4 is not None and threshold_validate(PK.hash_message(str(((id, L[j], j), 2, v4))),sig4):
            output.put_nowait(v4)
        if v3 is not None and j > lock and threshold_validate(PK.hash_message(str(((id, L[j], j), 1, v3))),sig3):
            lock = j
        if v2 is not None and j > key[0] and threshold_validate(PK.hash_message(str(((id, L[j], j), 0, v2))),sig2):
            key = (j, v2, sig2)


    def _recv():
        while True:
            (nodeid, (cmd, msg)) = receive()

            # message dispatcher
            if cmd == 'send':
                handle_broadcast(msg, nodeid)
            elif cmd == 'ack':
                handle_ack(msg, nodeid)
            elif cmd == 'done':
                handle_done(msg, nodeid)
            elif cmd == 'skip_share':
                handle_skip_share(msg, nodeid)
            elif cmd == 'skip':
                handle_skip(msg, nodeid)
            elif cmd == 'view_change':
                handle_view_change(msg, nodeid)

    def ex_sbc_validation(id, pid, j, rounds, v, sig_ex, sig_in):
        if rounds == 0 and ex_bc_validation(id, pid, j, v, sig_ex):
            return True
        h = PK.hash_message(str(((id, pid, j), rounds - 1, v)))
        if rounds > 0 and threshold_validate(h, sig_in):
            return True
        return False

    def ex_bc_validation(id, pid, j, v, sig_ex):
        # TODO: add external validation logic
        return True

    def threshold_validate(h, sig_in):
        try:
            PK.verify_signature(sig_in, h)
            return True
        except AssertionError:
            print("threshold_validate failure!")
            return False

    def share_validate(sig_share, nodeid, h):
        try:
            PK.verify_share(sig_share, nodeid, h)
            return True
        except AssertionError:
            return False

    def pbbroadcast():
        nonlocal id, pid, j, v, sig
        sig_in = None
        for rounds in range(4):
            print("View %d: rounds %d broadcast start\n" % (j, rounds))
            broadcast(('send', ((id, pid, j), rounds, (v[j], (sig[j], sig_in)))))
            sig_in = broadcast_sig_queue.get()
        broadcast_output_queue.put_nowait(sig_in)


    Greenlet(_recv).start()
    while True:
        # Broadcast Phase
        Greenlet(pbbroadcast).start()

        # wait for skip messages
        while broadcast_output_queue.empty() and not skip[j]:
            gevent.sleep(0)
        if not skip[j]:
            broadcast(('done', (id, j, (v[j], broadcast_output_queue.get()))))
        while not skip[j]:
            gevent.sleep(0)
        # logger.debug(f'Broadcast Result Dkey: {Dkey}\n Dlock: {Dlock}\n Dcommit: {Dcommit}',
        #              extra={'nodeid': pid, 'epoch': j})

        # abandon all the broadcast
        for k in range(N):
            for rounds in range(4):
                stop[k][j][rounds] = True

        # leader election
        if L[j] is None:
            L[j] = election(j)

        broadcast(('view_change', (id, j, Dkey[L[j]][j],Dlock[L[j]][j], Dcommit[L[j]][j])))

        while view_change_count[j] <= 2 * f + 1:
            gevent.sleep(0)

        v[j + 1] = key[1]
        sig[j + 1] = (key[0], key[2])
        j += 1

        if not output.empty():
            return output.get()
