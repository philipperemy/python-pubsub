import sys

from tqdm import tqdm

from pubsub import MessageQueue

m = MessageQueue()
m.connect()
m.subscribe('random')

for i in tqdm(range(int(1e7)), desc='Benchmarking', file=sys.stdout, unit_scale=True, unit=' msg'):
    m.get_message(timeout=None)
