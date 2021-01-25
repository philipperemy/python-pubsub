from pubsub import MessageQueue


def main():
    m = MessageQueue()
    m.connect()
    while True:
        m.send_message('random', f'My message {i}.')


if __name__ == '__main__':
    main()
