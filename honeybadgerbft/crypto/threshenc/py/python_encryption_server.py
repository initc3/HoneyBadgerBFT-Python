#!/usr/bin/env python3

import sys
# your gen-py dir
sys.path.append('../thrift/gen-py')

import argparse

from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket
from thrift.transport import TTransport

from python_encryption_handler import PythonEncryptionHandler
from encryption import TPKEService

PYTHON_ENCRYPTION_DEFAULT_PORT = 9090

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python encryption server')
    parser.add_argument('--port',
                        type=int,
                        default=PYTHON_ENCRYPTION_DEFAULT_PORT,
                        help='Python Encryption Server port')
    parsed_args = parser.parse_args()
    port = parsed_args.port

    handler = PythonEncryptionHandler()
    processor = TPKEService.Processor(handler)
    transport = TSocket.TServerSocket(port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

    # You could do one of these for a multithreaded server
    # server = TServer.TThreadedServer(
    #     processor, transport, tfactory, pfactory)
    # server = TServer.TThreadPoolServer(
    #     processor, transport, tfactory, pfactory)

    print('Starting the server...')
    server.serve()
    print('done.')