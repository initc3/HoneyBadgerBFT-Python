import random
from collections import defaultdict
import math
import datetime

import gevent
from gevent.event import Event
from gevent.queue import Queue
from pytest import fixture, mark, raises

from logging import getLogger
from our_srcs.consts import *
from our_srcs.utils import *

from honeybadgerbft.core.honeybadger import HoneyBadgerBFT, ImprovedHoneyBadgerBFT, PermutedHoneyBadgerBFT, RandomizedHoneyBadgerBFT
HONEYBADGERS = [("Ordered Honeybadger", HoneyBadgerBFT), ("Permuted Honeybadger", PermutedHoneyBadgerBFT),  ("Randomized Honeybadger", RandomizedHoneyBadgerBFT), ("Parity Honeybadger", ImprovedHoneyBadgerBFT)]
setup_logging()
logger = getLogger(LOGGER_NAME)

### Test asynchronous common subset
@mark.parametrize("HB", HONEYBADGERS)
@mark.parametrize("N", NUM_OF_NODE_OPTIONS)
@mark.parametrize("identical_inputs", NUM_OF_IDENTICAL_INPUTS_OPTIONS)
@mark.parametrize("input_sizes", INPUT_SIZES)
def test_honeybadger_full(HB, N, identical_inputs, input_sizes):
    if N < identical_inputs:
        logger.debug("There can't be more identical_inputs than number of nodes, skipping test")
        return    
    
    logger.info(f"Running Honeybadger test with parameters:\n\tHoneyBadger: {HB[0]}\n\tNumber of Nodes: {N}\n\tNumber of Identical Inputs: {identical_inputs}\n\tInput Sizes: {input_sizes}")

    badgers, threads = setup_honeybadgers(HB[1], N)

    time_at_start = datetime.datetime.now().timestamp()
    
    for iter_index in range(NUM_OF_INPUTS_IN_ITERATION):
        identical_hbs = random.sample(range(N), identical_inputs)
        logger.debug(f"At epoch {iter_index} chose identical_inputs {identical_hbs}")
        for node_index in range(N):
            if node_index in identical_hbs:
                badgers[node_index].submit_tx(f'<HBBFT Input Epoch {iter_index} Identical Input> ' + 'a'*input_sizes)
            else:
                badgers[node_index].submit_tx(f'<HBBFT Input Epoch {iter_index} Different Input {node_index} ' + 'a'*input_sizes)


    logger.debug("Done submitting all inputs")

    try:
        outs = [threads[i].get() for i in range(N)]

        # Consistency check
        assert len(set(outs)) == 1

        time_at_end = datetime.datetime.now().timestamp()
        time_diff = time_at_end - time_at_start
        logger.info(f"Time passed: {time_diff}")
        result = str(time_diff)[:4]
        logger.critical(f"Result: {result} (params {HB[0]}, {N}, {identical_inputs}, {input_sizes})")
        return str(time_diff)[:4]

    except KeyboardInterrupt:
        gevent.killall(threads)
        raise

