import logging
from collections import defaultdict

import gevent
from gevent.event import AsyncResult, Event
from gevent.queue import Queue

from honeybadgerbft.exceptions import RedundantMessageError


logger = logging.getLogger(__name__)

a0, a1, bob, x = 0, 1, 2, 3


def byz_ba_issue_59(sid, pid, N, f, coin, input, decide, broadcast, receive):
    """Modified binary consensus from [MMR14], so that it exhibits a
    byzantine behavior as per issue #59
    (see https://github.com/amiller/HoneyBadgerBFT/issues/59).

    :param sid: session identifier
    :param pid: my id number
    :param N: the number of parties
    :param f: the number of byzantine parties
    :param coin: a ``common coin(r)`` is called to block until receiving a bit
    :param input: ``input()`` is called to receive an input
    :param decide: ``decide(0)`` or ``output(1)`` is eventually called
    :param broadcast: broadcast channel
    :param receive: receive channel
    :return: blocks until
    """
    # Messages received are routed to either a shared coin, the broadcast, or AUX
    est_values = defaultdict(lambda: [set(), set()])
    aux_values = defaultdict(lambda: [set(), set()])
    conf_values = defaultdict(lambda: {(0,): set(), (1,): set(), (0, 1): set()})
    est_sent = defaultdict(lambda: [False, False])
    conf_sent = defaultdict(lambda: {(0,): False, (1,): False, (0, 1): False})
    bin_values = defaultdict(set)

    # This event is triggered whenever bin_values or aux_values changes
    bv_signal = Event()

    def _recv():
        while True:  # not finished[pid]:
            (sender, msg) = receive()
            logger.debug(f'receive {msg} from node {sender}',
                         extra={'nodeid': pid, 'epoch': msg[1]})
            assert sender in range(N)
            if msg[0] == 'EST':
                # BV_Broadcast message
                _, r, v = msg
                assert v in (0, 1)
                if sender in est_values[r][v]:
                    print('Redundant EST received', msg)
                    raise RedundantMessageError(
                        'Redundant EST received {}'.format(msg))

                est_values[r][v].add(sender)
                # Relay after reaching first threshold
                if len(est_values[r][v]) >= f + 1 and not est_sent[r][v]:
                    est_sent[r][v] = True
                    for receiver in range(N):
                        logger.debug(
                            f"broadcast {('EST', r, v)} to node {receiver}",
                            extra={'nodeid': pid, 'epoch': r})
                        if receiver != 2:
                            broadcast(('EST', r, v), receiver=receiver)

                # Output after reaching second threshold
                if len(est_values[r][v]) >= 2 * f + 1:
                    logger.debug(
                        f'add v = {v} to bin_value[{r}] = {bin_values[r]}',
                        extra={'nodeid': pid, 'epoch': r},
                    )
                    bin_values[r].add(v)
                    logger.debug(f'bin_values[{r}] is now: {bin_values[r]}',
                                 extra={'nodeid': pid, 'epoch': r})
                    bv_signal.set()

            elif msg[0] == 'AUX':
                # Aux message
                _, r, v = msg
                assert v in (0, 1)
                if sender in aux_values[r][v]:
                    print('Redundant AUX received', msg)
                    raise RedundantMessageError(
                        'Redundant AUX received {}'.format(msg))

                aux_values[r][v].add(sender)
                logger.debug(
                    f'add v = {v} to aux_value[{r}] = {aux_values[r]}',
                    extra={'nodeid': pid, 'epoch': r},
                )

                bv_signal.set()

            elif msg[0] == 'CONF':
                # CONF message
                _, r, v = msg
                assert v in ((0,), (1,), (0, 1))
                if sender in conf_values[r][v]:
                    # FIXME: raise or continue? For now will raise just
                    # because it appeared first, but maybe the protocol simply
                    # needs to continue.
                    print(f'Redundant CONF received {msg} by {sender}')
                    raise RedundantMessageError(
                        f'Redundant CONF received {msg} by {sender}')

                conf_values[r][v].add(sender)
                logger.debug(
                    f'add v = {v} to conf_value[{r}] = {conf_values[r]}',
                    extra={'nodeid': pid, 'epoch': r},
                )

                bv_signal.set()

    # Run the receive loop in the background
    gevent.spawn(_recv)

    # Block waiting for the input
    vi = input()
    assert vi in (0, 1)
    est = vi
    r = 0
    while True:  # Unbounded number of rounds
        logger.info(f'starting round {r} with est set to {est}',
                    extra={'nodeid': pid, 'epoch': r})
        not_est = int(not bool(est))
        if not est_sent[r][est]:
            est_sent[r][est] = True
            est_sent[r][not_est] = True
            logger.debug(
                f"broadcast {('EST', r, int(not bool(est)))} to node {0}",
                extra={'nodeid': pid, 'epoch': r},
            )
            broadcast(('EST', r, int(not bool(est))), receiver=0)
            logger.debug(
                f"broadcast {('EST', r, est)} to node {1}",
                extra={'nodeid': pid, 'epoch': r},
            )
            broadcast(('EST', r, est), receiver=1)

        while len(bin_values[r]) == 0:
            # Block until a value is output
            bv_signal.clear()
            bv_signal.wait()

        w = next(iter(bin_values[r]))  # take an element
        logger.debug(f"broadcast {('AUX', r, w)}",
                     extra={'nodeid': pid, 'epoch': r})
        for receiver in range(N):
            if receiver != 2:
                broadcast(('AUX', r, w), receiver=receiver)

        # After this all messages within A are delivered and x sends both
        # BVAL(0) and BVAL(1) to every node in A. Thus every node in A
        # broadcasts both BVAL(0) and BVAL(1) and sets bin_values={0,1}.
        logger.debug(
            'x sends both BVAL(0) and BVAL(1) to every node in A.',
            extra={'nodeid': pid, 'epoch': r},
        )
        broadcast(('EST', r, est), receiver=0)
        broadcast(('EST', r, int(not bool(est))), receiver=1)

        # XXX CONF phase
        if not conf_sent[r][(0, 1)]:
            conf_sent[r][(0, 1)] = True
            logger.debug(f"broadcast {('CONF', r, (0, 1))}",
                         extra={'nodeid': pid, 'epoch': r})
            broadcast(('CONF', r, (0, 1)))

        logger.info(
            f'Block until receiving the common coin value',
            extra={'nodeid': pid, 'epoch': r},
        )
        # Block until receiving the common coin value
        s = coin(r)
        logger.debug(f's = coin(r) | s = {s}, r = {r}',
                     extra={'nodeid': pid, 'epoch': r})
        not_s = int(not bool(s))

        logger.debug(f"broadcast {('EST', r, not_s)} to node 2",
                     extra={'nodeid': pid, 'epoch': r})
        broadcast(('EST', r, not_s), receiver=2)
        logger.debug(f"broadcast {('AUX', r, not_s)} to node 2",
                     extra={'nodeid': pid, 'epoch': r})
        broadcast(('AUX', r, not_s), receiver=2)
        logger.info(f'exiting round {r}, setting est = s ({s})',
                    extra={'nodeid': pid, 'epoch': r})
        est = s
        r += 1


class SendCondition(Event):

    epoch = 0
    priority = None
    value = None


class NetworkScheduler:
    COIN_PHASE_BEGIN = 18
    LAST = 24
    NO_DELAY = None

    def __init__(self, *, receivers):
        self.queues = [Queue() for _ in range(4)]
        self.receivers = receivers
        self.events = defaultdict(SendCondition)
        self.coins = defaultdict(AsyncResult)
        self.initial_values = defaultdict(AsyncResult)
        self.initial_values[0].set(0)

    def consume_queue(self, queue):
        for m in queue:
            gevent.spawn(self.schedule, m)

    def schedule(self, message):
        # TODO once get_events() is implemented
        # event, next_event = self.get_events(message)
        sender, receiver, (tag, epoch, bin_value) = message
        priority = self.get_priority(message)

        if priority == self.COIN_PHASE_BEGIN:
            coin = int(not bool(bin_value))
            self.coins[epoch].set(coin)
            self.initial_values[epoch + 1].set(coin)

        if priority == self.LAST:
            next_event_priority = 0
            next_event_epoch = epoch + 1
        elif priority is not self.NO_DELAY:
            next_event_priority = priority + 1
            next_event_epoch = epoch

        try:
            next_event = self.events[next_event_epoch, next_event_priority]
        except NameError:
            next_event = None
        else:
            next_event.priority = next_event_priority
            next_event.epoch = next_event_epoch

        event = self.events[epoch, priority]
        event.epoch = epoch
        event.priority = priority
        event.value = bin_value

        logger.debug(f'Schedule message {message} with priority {priority}.',
                     extra={'nodeid': message[0], 'epoch': message[2][1]})
        gevent.spawn(self.send, message, event=event, next_event=next_event)

    def send(self, message, *, event, next_event):
        sender, receiver, (tag, epoch, value) = message
        logger.info(
            f'Wait for condition {event} with priority {event.priority} for'
            f'epoch {event.epoch} and value {event.value}',
            extra={'nodeid': sender, 'epoch': epoch},
        )
        event.wait()
        logger.info(f'Send message {message} --- PRIORITY: {event.priority}',
                    extra={'nodeid': sender, 'epoch': epoch})
        self.receivers[receiver].put((sender, (tag, epoch, value)))
        if next_event:
            logger.info(
                f'Set (ready) condition {next_event} with priority'
                f'{next_event.priority} for epoch {next_event.epoch}'
                f'and value {event.value}',
                extra={'nodeid': sender, 'epoch': epoch},
            )
            next_event.set()

            # Move to next round.
            if next_event.priority == self.LAST:
                self.events[next_event.epoch + 1, self.NO_DELAY].set()

    def get_priority(self, message):
        message_map = self.get_message_map(message)
        _, receiver, (tag, epoch, _) = message
        try:
            priority = message_map[message]
        except KeyError:
            if tag == 'CONF' or receiver == x:
                priority = self.NO_DELAY
            else:
                priority = self.LAST
        return priority

    def get_events(self, message):
        raise NotImplementedError

    def get_message_map(self, message):
        sender, receiver, (tag, epoch, _) = message
        if self.is_a_coin_dependent_message(
                sender=sender, receiver=receiver, tag=tag):
            message_map = self.coin_dependent_message_map(epoch)
        else:
            message_map = self.coin_independent_message_map(epoch)
        return message_map

    def coin_independent_message_map(self, epoch):
        r = epoch
        v = self.initial_values[r].get()
        not_v = int(not bool(v))
        msg_map = {
            (x, a0, ('EST', r, not_v)): 0,
            (x, a1, ('EST', r, v)): 1,
            (bob, a0, ('EST', r, not_v)): 2,
            (bob, a1, ('EST', r, not_v)): 3,
            (a0, a0, ('EST', r, v)): 4,
            (a0, a0, ('EST', r, not_v)): 5,
            # ...
            (a1, a1, ('EST', r, v)): 6,
            (a0, a1, ('EST', r, v)): 7,
            # ...
            (a1, a0, ('EST', r, v)): 8,
            (a0, a1, ('EST', r, not_v)): 9,
            (a0, a0, ('AUX', r, not_v)): 10,
            (a0, a1, ('AUX', r, not_v)): 11,
            (a1, a0, ('AUX', r, v)): 12,
            (a1, a1, ('AUX', r, v)): 13,
            # ...
            (x, a0, ('EST', r, v)): 14,
            (x, a1, ('EST', r, not_v)): 15,
            (x, a0, ('AUX', r, not_v)): 16,
            (x, a1, ('AUX', r, not_v)): 17,
            # not_coin phase - one of these two messages is sent to B, such
            # that the value is the boolean NOT of the coin value
            (x, bob, ('EST', r, 0)): 18,
            (x, bob, ('EST', r, 1)): 18,
        }
        return msg_map

    def coin_dependent_message_map(self, epoch):
        """Messages for which the scheduling depends on the value of
        the coin.
        """
        coin = self.coins[epoch].get()
        not_coin = int(not bool(coin))
        return {
            (a0, bob, ('EST', epoch, not_coin)): 19,
            (a1, bob, ('EST', epoch, not_coin)): 20,
            (a0, bob, ('AUX', epoch, not_coin)): 21,
            (a1, bob, ('AUX', epoch, not_coin)): 21,
            (bob, bob, ('AUX', epoch, not_coin)): 22,
            (x, bob, ('AUX', epoch, not_coin)): 23,
        }

    def is_a_coin_dependent_message(self, *, sender, receiver, tag):
        """Checks if the message depends on the value of the coin for
        its scheduling.
        """
        return receiver == bob and (tag == 'AUX' or
                                    sender in (a0, a1) and tag == 'EST')

    def start(self):
        for queue in self.queues:
            gevent.spawn(self.consume_queue, queue)
        self.events[0, 0].set()
        self.events[0, self.NO_DELAY].set()


def broadcast_router(N):
    """Router controlled by an adversary such that incoming messages are
    redirected to the queues of an adversarial network scheduler.

    :return: (receives, sends)
    """
    queues = [Queue() for _ in range(N)]
    ns = NetworkScheduler(receivers=queues)
    ns.start()

    def makeBroadcast(i):
        def _send(j, o):
            ns.queues[i].put((i, j, o))

        def _bc(o, receiver=None):
            if receiver is not None:
                _send(receiver, o)
            else:
                for j in range(N):
                    _send(j, o)

        return _bc

    def makeRecv(j):
        def _recv():
            i, o = queues[j].get()
            return i, o
        return _recv

    return ([makeBroadcast(i) for i in range(N)],
            [makeRecv(j) for j in range(N)])
