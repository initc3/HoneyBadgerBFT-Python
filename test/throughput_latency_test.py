import random
from collections import defaultdict
import math
import datetime
from gevent import monkey
monkey.patch_all()
import gevent
from gevent.event import Event
from gevent.queue import Queue
from pytest import fixture, mark, raises

from logging import getLogger
from our_srcs.consts import *
from our_srcs.utils import *

from honeybadgerbft.core.honeybadger import HoneyBadgerBFT, ImprovedHoneyBadgerBFT, PermutedHoneyBadgerBFT, RandomizedHoneyBadgerBFT, DistanceHoneyBadgerBFT
HONEYBADGERS = [("Ordered Honeybadger", HoneyBadgerBFT), ("Permuted Honeybadger", PermutedHoneyBadgerBFT),  ("Randomized Honeybadger", RandomizedHoneyBadgerBFT), ("Parity Honeybadger", ImprovedHoneyBadgerBFT), ("Distance Honeybadger", DistanceHoneyBadgerBFT)]
setup_logging()
logger = getLogger(LOGGER_NAME)

@mark.parametrize("HB", HONEYBADGERS)
@mark.parametrize("N", NUM_OF_NODE_OPTIONS)
@mark.parametrize("identical_inputs", NUM_OF_IDENTICAL_INPUTS_OPTIONS)
@mark.parametrize("input_sizes", INPUT_SIZES)
def test_honeybadger_full(HB, N, identical_inputs, input_sizes):
    if N < identical_inputs:
        logger.debug("There can't be more identical_inputs than number of nodes, skipping test")
        return   
    if (N != SET_NUM_OF_NODES and identical_inputs != SET_NUM_OF_IDENTICAL_INPUTS) or (N != SET_NUM_OF_NODES and input_sizes != SET_INPUT_SIZE) or (identical_inputs != SET_NUM_OF_IDENTICAL_INPUTS and input_sizes != SET_INPUT_SIZE):
        logger.debug("Not an interesting test, skipping")
        return
    
    logger.info(f"Running Honeybadger test with parameters:\n\tHoneyBadger: {HB[0]}\n\tNumber of Nodes: {N}\n\tNumber of Identical Inputs: {identical_inputs}\n\tInput Sizes: {input_sizes}")

    txs_to_submit = [[] for i in range(N)]
    for iter_index in range(NUM_OF_INPUTS_IN_ITERATION):
        identical_hbs = random.sample(range(N), identical_inputs)
        logger.debug(f"At epoch {iter_index} chose identical_inputs {identical_hbs}")
        for node_index in range(N):
            if node_index in identical_hbs:
                txs_to_submit[node_index].append(f'<HBBFT Input Epoch {iter_index} Identical Input> ' + 'a'*input_sizes)
            else:
                txs_to_submit[node_index].append(f'<HBBFT Input Epoch {iter_index} Different Input {node_index} ' + 'a'*input_sizes)
    amount_of_distinct_messages = len(set([msg for l in txs_to_submit for msg in l]))
    logger.debug(f"Number of distinct message is {amount_of_distinct_messages}")

    badgers, threads = setup_honeybadgers(HB[1], N, amount_of_distinct_messages)

    time_at_start = datetime.datetime.now().timestamp()

    for node_index in range(N):
        for tx in txs_to_submit[node_index]:
            badgers[node_index].submit_tx(tx)

    logger.debug("Done submitting all inputs")

    try:
        outs = [threads[i].get() for i in range(N)]
        # Consistency check
        assert len(set(outs)) == 1
        
        time_at_end = datetime.datetime.now().timestamp()
        time_diff = time_at_end - time_at_start
        logger.info(f"Time passed: {time_diff}")
        result = str(round(time_diff, 2))


        total_bytes_sent = 0
        for b in badgers:
            total_bytes_sent += b.get_bytes_sent()
        logger.critical(f"Result: bytes_sent={total_bytes_sent},total_time={result} (params {HB[0]}, {N}, {identical_inputs}, {input_sizes})")

        gevent.killall(threads)
        del badgers

    except KeyboardInterrupt:
        gevent.killall(threads)
        raise

