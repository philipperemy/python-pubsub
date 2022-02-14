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

import json
import logging
import os

str_type = str
from configparser import ConfigParser, NoOptionError, NoSectionError

loggers = dict()


class ConnectionClosed(Exception):
    pass


class ProtocolError(Exception):
    pass


class CoreConfigParser(ConfigParser, object):
    def get(self, section, option, default=None):
        try:
            return super(CoreConfigParser, self).get(section, option)
        except (NoOptionError, NoSectionError):
            return default


def construct_message(queue, message):
    if not isinstance(queue, str_type):
        raise ValueError('Queue name must be a string, not %s' % queue)

    if len(queue) < 1:
        raise ValueError('Queue name must be at least one character in length')

    if ' ' in queue:
        raise ValueError('Queue name must not contain spaces')

    if isinstance(message, str_type):
        message = dict(coremq_string=message)

    if isinstance(message, dict):
        message = json.dumps(message)
    else:
        raise ValueError('Messages should be either a dictionary or a string')

    if len(message) > 99999999:  # 100 MB max int that can fit in message header (8 characters, plus two controls)
        raise ValueError('Message cannot be 100MB or larger')

    if not isinstance(message, bytes):
        message = message.encode('utf-8')

    return ('+%s %s ' % (len(message) + len(queue) + 1, queue)).encode('utf-8') + message


def send_message(socket, queue, message):
    socket.send(construct_message(queue, message))


def get_message(socket, timeout=1):
    socket.settimeout(timeout)
    data = socket.recv(10).decode('utf-8')
    expected_length, data = validate_header(data)

    while len(data) < expected_length:
        data += socket.recv(expected_length - len(data)).decode('utf-8')

    if ' ' not in data:
        return None, data

    queue, message = data.split(' ', 1)
    return queue, json.loads(message)


def validate_header(data):
    """
    Validates that data is in the form of "+5 Hello", with + beginning messages, followed by the length of the
    message as an integer, followed by a space, then the message.
    :param data: The raw data from the socket
    :return: (int, str) - the expected length of the message, the message
    """
    if not data:
        raise ConnectionClosed()

    if data[0] != '+':
        raise ProtocolError('Missing beginning +')

    if ' ' not in data:
        raise ProtocolError('Missing space after length')

    length, data = data.split(' ', 1)

    try:
        length = int(length[1:])
    except ValueError:
        raise ProtocolError('Length integer must be between + and space')

    return length, data


def load_configuration(path=None):
    """
    Loads configuration for CoreMQ and CoreWS servers
    :param path: Optional path for the config file. Defaults to current directory
    :return: CoreConfigParser
    """
    if not path:
        path = os.path.join(os.getcwd(), 'coremq.conf')

    c = CoreConfigParser()

    try:
        c.read(path)
    except:
        logging.error('Config file could not be loaded')

    return c


def get_logger(config, section, logger_name=None):
    """
    Configures the Python logging module based on the configuration settings from load_configuration
    :param config:  The CoreConfigParser instance from load_configuration
    :param section: The section where the logging config can be found
    :param logger_name: The name of the logger. Uses section by default
    :return: Logger
    """
    logging.basicConfig()

    if section in loggers:
        return loggers[section]

    logger = logging.getLogger(section or logger_name)
    logger.propagate = False

    log_file = config.get('CoreMQ', 'log_file', 'stdout')
    if log_file == 'stdout':
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(log_file)

    log_level = config.get('CoreMQ', 'log_level', 'DEBUG')
    logger.setLevel(logging.getLevelName(log_level))

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    loggers[section] = logger
    return logger


def comma_string_to_list(s):
    """
    Takes a line of values, seprated by commas and returns the values in a list, removing any extra whitespacing.
    :param s: The string with commas
    :return: list
    """
    if isinstance(s, (list, tuple)):
        return s

    result = []
    items = s.split(',')
    for i in items:
        result.append(i.strip())

    return result
