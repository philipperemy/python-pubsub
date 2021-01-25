import random

from pubsub import MessageQueue


def prime_numbers():
    for num in range(1, 1001):
        for i in range(2, num):
            if num % i == 0:
                break
        else:
            yield num


def main():
    m = MessageQueue()
    m.connect()
    print(m.welcome_message)
    pub_id = random.randint(0, 1000)
    print(f'Publisher ID: {pub_id}.')

    def publish(channel, msg):
        msg += f' Publisher Id is [{pub_id}].'
        print(f'PUBLISH: {msg}.')
        m.send_message(channel, msg)

    for prime in prime_numbers():
        publish('prime', f'Next prime number is [{prime}].')
        publish('random', f'Next random number is [{random.randint(0, 10000)}].')


if __name__ == '__main__':
    main()
