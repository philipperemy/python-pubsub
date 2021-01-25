"""
CoreMQ
------
A pure-Python messaging queue.

License
-------
The MIT License (MIT)
Copyright (c) 2015 Ross Peoples <ross.peoples@gmail.com>
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import collections
import signal
import socket
import sys
import time
import uuid
from multiprocessing import Process
from socketserver import BaseRequestHandler, ThreadingMixIn, TCPServer
import traceback
from pubsub.common import ConnectionClosed, get_message, send_message

ADDRESS = '0.0.0.0'
PORT = 6747  # spells MSGQ (message queue)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    EXITING = False
    PROCESS = None
    HISTORY = dict()


class TCPRequestHandler(BaseRequestHandler):
    connections = dict()

    def handle(self):
        conn_id = str(uuid.uuid4())
        TCPRequestHandler.connections[conn_id] = dict(handler=self, subscriptions=[conn_id], options=dict())
        self.respond(conn_id, 'Welcome!')

        print('Clients connected: %s' % len(TCPRequestHandler.connections))
        while True:
            try:
                queue, message = get_message(self.request)
                message['coremq_sender'] = conn_id
                message['coremq_sent'] = time.time()

                if 'coremq_subscribe' in message:
                    self.subscribe(conn_id, message['coremq_subscribe'])
                    self.respond(conn_id, 'OK: Subscribe successful')
                elif 'coremq_unsubscribe' in message:
                    self.unsubscribe(conn_id, message['coremq_unsubscribe'])
                    self.respond(conn_id, 'OK: Unsubscribe successful')
                elif 'coremq_options' in message:
                    self.set_options(conn_id, message['coremq_options'])
                    self.respond(conn_id, 'OK: Options set')
                elif 'coremq_gethistory' in message:
                    self.get_history(conn_id, message['coremq_gethistory'])
                else:
                    self.respond(conn_id, 'OK: Message sent')
                    self.broadcast(queue, message)
                    self.store_message(queue, message)

            except socket.timeout:
                pass
            except (ConnectionClosed, socket.error):
                break
            except Exception as ex:
                self.respond(conn_id, str(ex))
                print(conn_id, ex)
                traceback.print_exc()

        try:
            self.respond(conn_id, 'BYE')
        except socket.error:
            pass

        if conn_id in TCPRequestHandler.connections:
            del TCPRequestHandler.connections[conn_id]

        print('Clients connected: %s' % len(TCPRequestHandler.connections))

    def respond(self, conn_id, text):
        send_message(self.request, conn_id, dict(response=text))

    def subscribe(self, conn_id, queues):
        if not queues:
            return

        if conn_id not in TCPRequestHandler.connections:
            return

        if not isinstance(queues, (list, tuple)):
            queues = [queues]

        subs = TCPRequestHandler.connections[conn_id]['subscriptions']
        for q in queues:
            if q not in subs:
                subs.append(q)

    def unsubscribe(self, conn_id, queues):
        if not queues:
            return

        if conn_id not in TCPRequestHandler.connections:
            return

        if not isinstance(queues, (list, tuple)):
            queues = [queues]

        subs = TCPRequestHandler.connections[conn_id]['subscriptions']
        for q in queues:
            if q in subs:
                subs.remove(q)

    def set_options(self, conn_id, options):
        opts = TCPRequestHandler.connections[conn_id]['options']
        opts.update(options)

        for key, val in options.items():
            if val is None and key in opts:
                del opts[key]

    def broadcast(self, queue, message):
        for conn_id, d in TCPRequestHandler.connections.items():
            if conn_id == message['coremq_sender'] and queue != conn_id and d['options'].get('echo', False) is False:
                continue

            if queue in d['subscriptions']:
                send_message(d['handler'].request, queue, message)

    def store_message(self, queue, message):
        if not queue in ThreadedTCPServer.HISTORY:
            ThreadedTCPServer.HISTORY[queue] = collections.deque(maxlen=10)

        ThreadedTCPServer.HISTORY[queue].append(message)

    def get_history(self, conn_id, queues):
        result = dict()
        for q in queues:
            if q in ThreadedTCPServer.HISTORY:
                result[q] = list(ThreadedTCPServer.HISTORY[q])

        send_message(self.request, conn_id, dict(response=result))


def signal_handler(signal, frame):
    print('Shutting down message queue')
    ThreadedTCPServer.EXITING = True


def message_queue_process():
    print('Starting message queue')
    server = ThreadedTCPServer((ADDRESS, PORT), TCPRequestHandler)
    server.timeout = 1
    while not ThreadedTCPServer.EXITING:
        server.handle_request()

    print('Message queue stopped')
    sys.exit(0)


def start():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    ThreadedTCPServer.PROCESS = Process(target=message_queue_process)
    ThreadedTCPServer.PROCESS.start()


if __name__ == '__main__':
    start()
