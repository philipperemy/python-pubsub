from pubsub import MessageQueue


def main():
    m = MessageQueue()
    m.connect()
    for i in range(int(1e7)):
        m.send_message('random', f'My message {i}.')


if __name__ == '__main__':
    main()
