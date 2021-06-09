from pubsub import MessageQueue

# Start the broker with the command: start_pubsub_broker

m = MessageQueue()
m.connect()
m.subscribe('prime')
m.subscribe('random')
while True:
    channel, message = m.get_message(timeout=None)
    print(f'RECEIVE: channel: {channel}, message: {message["coremq_string"]}')
