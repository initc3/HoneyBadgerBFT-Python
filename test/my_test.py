import random
from collections import defaultdict
import math
import datetime

import gevent
from gevent.event import Event
from gevent.queue import Queue
from pytest import fixture, mark, raises

from logging import getLogger
from our_srcs.utils import *
from our_srcs.consts import *

setup_logging()
logger = getLogger(LOGGER_NAME)

def test_main():
    #_test_num_of_nodes()
    _test_num_of_identical_inputs()
    #_test_input_sizes()


def _test_num_of_nodes():
    logger.info("Testing Number of Nodes")
    for num_of_nodes in NUM_OF_NODE_OPTIONS:
        _test_honeybadgers(num_of_nodes, DEFAULT_NUM_OF_IDENTICAL_INPUTS_OPTIONS, DEFAULT_INPUT_SIZE)

def _test_num_of_identical_inputs():
    logger.info("Testing different identical inputs")
    for num_of_identical_inputs in NUM_OF_IDENTICAL_INPUTS_OPTIONS:

def _test_honeybadgers(num_of_nodes, identical_input, input_size):
    logger.info(f"Test Honeybadgers with N={num_of_nodes}, id={identical_input}, size={input_size}")
    for hb_tuple in HONEYBADGERS:
        logger.info("Testing Honeybadger: {}".format(hb_tuple[0]))
        _test_honeybadger_full(hb_tuple[1], num_of_nodes, identical_input, input_size)

### Test asynchronous common subset
def _test_honeybadger_full(HB, N, identical_inputs, input_sizes):
    assert N >= identical_inputs, "There can't be more identical_inputs than number of nodes"
    
    badgers, threads = setup_honeybadgers(HB, N)

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

    except KeyboardInterrupt:
        gevent.killall(threads)
        raise

