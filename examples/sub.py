from pubsub import MessageQueue

# Start the broker with the command: start_pubsub_broker

m = MessageQueue()
m.connect()
count = 0
m.subscribe('prime')
m.subscribe('random')
while True:
    channel, message = m.get_message(timeout=None)

    if channel in ['prime', 'random']:
        count += 1
        print(f'RECEIVE {count}: channel: {channel}, message: {message["coremq_string"]}')
