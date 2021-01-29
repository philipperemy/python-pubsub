# Python PubSub
A simple python implementation of a message router with many subscribers and many publishers.

It can be considered as as fork of the project: [CoreMQ](https://github.com/deejross/coremq).

This implementation handles:
- 26K messages per second.
- `TCP_NODELAY` flag activated for latency sensitive applications.
- Many publishers.
- Many subscribers.
- Multiple channels.

```
pip install python-pubsub
```

Refer to the [examples](examples).
