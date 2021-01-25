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

import socket

from pubsub.common import get_message, send_message


class MessageQueue(object):
    def __init__(self, server='127.0.0.1', port=6747):
        self.server = server
        self.port = port
        self.socket = None
        self.connection_id = None
        self.welcome_message = None
        self.subscriptions = []
        self.options = dict()
        self.last_message_time = 0

    def connect(self):
        if self.socket:
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(30)
        self.socket.connect((self.server, self.port))
        self.connection_id, self.welcome_message = get_message(self.socket)

        if self.subscriptions:
            self.subscribe(*self.subscriptions)

        if self.options:
            self.set_options(**self.options)

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def send_message(self, queue, message):
        if not self.socket:
            self.connect()

        try:
            send_message(self.socket, queue, message)
        except socket.error:
            # attempt to reconnect if there was a connection error
            self.close()
            self.connect()
            send_message(self.socket, queue, message)

        try:
            return self.get_message()
        except socket.error:
            return None, None

    def get_message(self, timeout=1):
        if not self.socket:
            self.connect()

        try:
            queue, message = get_message(self.socket, timeout=timeout)
        except socket.timeout:
            return None, None
        except socket.error:
            # attempt to reconnect if there was a connection error
            self.close()
            self.connect()
            try:
                queue, message = get_message(self.socket, timeout=timeout)
            except socket.timeout:
                return None, None

        if 'response' in message and message['response'] == 'BYE':
            self.close()

        return queue, message

    def listen(self, seconds=30):
        for i in range(seconds):
            m = self.get_message()
            if m[0]:
                print(m[0], m[1])

    def stress(self, queue, count=10000, wait=0, silent=False):
        import time

        start_time = time.time()
        for i in range(count):
            self.send_message(queue, dict(iteration=i))
            if wait:
                time.sleep(wait)
        end_time = time.time()

        if not silent:
            print('Stress results:')
            print('Iterations: %s' % count)
            print('Forced wait time: %s' % wait)
            print('Time taken: %s seconds' % (end_time - start_time))
            print('Messages per second: %s' % (float(count) / (end_time - start_time)))

    def get_history(self, *queues):
        if not queues:
            queues = self.subscriptions

        if not queues:
            raise ValueError('Must pass at least one queue name')

        if not isinstance(queues, (list, tuple)):
            queues = [queues]

        return self.send_message(self.connection_id, dict(coremq_gethistory=queues))

    def subscribe(self, *queues):
        if not queues:
            raise ValueError('Must pass at least one queue name')

        if not isinstance(queues, (list, tuple)):
            queues = [queues]

        for q in queues:
            if q not in self.subscriptions:
                self.subscriptions.append(q)

        return self.send_message(self.connection_id, dict(coremq_subscribe=queues))

    def unsubscribe(self, *queues):
        if not queues:
            raise ValueError('Must pass at least one queue name')

        if not isinstance(queues, (list, tuple)):
            queues = [queues]

        for q in queues:
            if q in self.subscriptions:
                self.subscriptions.remove(q)

        return self.send_message(self.connection_id, dict(coremq_unsubscribe=queues))

    def set_options(self, **options):
        self.options.update(options)

        for key, val in options.items():
            if val is None and key in self.options:
                del self.options[key]

        return self.send_message(self.connection_id, dict(coremq_options=options))


def stress_worker(args):
    import random
    import time
    server, port, queue, count, wait, listen_only = args

    time.sleep(random.uniform(0, 1))
    m = MessageQueue(server, port)
    try:
        m.connect()
    except:
        time.sleep(1)
        m.connect()

    if listen_only:
        try:
            m.subscribe(queue)
            messages = 0
            null_msg = 0
            errors = 0
            for i in range(count):
                try:
                    msg = m.get_message(timeout=10)
                    if msg[0] is not None:
                        messages += 1
                    else:
                        null_msg += 1
                        if null_msg >= 2:
                            break
                except:
                    errors += 1
        except:
            return count, 1

        m.close()

        return count - messages, errors
    else:
        time.sleep(random.uniform(0, 1))
        errors = 0
        start_time = time.time()
        for i in range(count):
            try:
                m.send_message(queue, dict(iteration=i + 1))
                if wait:
                    time.sleep(wait)
            except:
                errors += 1

        end_time = time.time()

        m.close()
        return end_time - start_time, float(count) / (end_time - start_time), errors


def parallel_stress(server, port, queue, count=1000, wait=0.01, workers=10, listeners=90):
    import multiprocessing

    print('Beginning stress test with these settings:')
    print('Server: %s' % server)
    print('Queue: %s' % queue)
    print('Count per worker: %s' % count)
    print('Delay between messages: %s' % wait)
    print('Number of workers: %s' % workers)
    print('Number of listeners: %s' % listeners)
    print('')

    pool1 = multiprocessing.Pool(listeners)
    pool2 = multiprocessing.Pool(workers)
    tasks1 = [(server, port, queue, count, wait, True) for i in range(listeners)]
    tasks2 = [(server, port, queue, count, wait, False) for i in range(workers)]

    job1 = pool1.map_async(stress_worker, tasks1)
    job2 = pool2.map_async(stress_worker, tasks2)
    job1.wait()
    job2.wait()
    listen_results = job1.get()
    worker_results = job2.get()
    slowest = 0
    fastest = 9999
    average_mps = 0
    errors = 0
    missed = 0

    for t, mps, errs in worker_results:
        if t > slowest:
            slowest = t

        if t < fastest:
            fastest = t

        average_mps += mps
        errors += errs

    average_mps /= float(workers)

    for m, errs in listen_results:
        missed += m

    print('Test results:')
    print('Total count: %s' % (count * workers))
    print('Fastest worker: %s seconds' % fastest)
    print('Slowest worker: %s seconds' % slowest)
    print('Number of errors: %s' % errors)
    print('Number of missing messages: %s' % missed)
    print('Average messages per second: %s' % average_mps)
