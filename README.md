# Python PubSub
A simple python implementation of a message router with many subscribers and many publishers.

It can be considered as as fork of the project: [CoreMQ](https://github.com/deejross/coremq).

<center>
<div><a href='//sketchviz.com/@philipperemy/8f597379f217ca0b6a20700ebc7f0b22'><img src='https://sketchviz.com/@philipperemy/8f597379f217ca0b6a20700ebc7f0b22/765f0d983410a72083cd967e7e0535dee8f9bcfc.sketchy.png' style='max-width: 100%;'></a></div>
</center>

This implementation handles:
- 26K messages per second.
- Latency of around 1ms.
- `TCP_NODELAY` flag activated for latency sensitive applications.
- Many publishers.
- Many subscribers.
- Multiple channels.

```
pip install python-pubsub
```

Refer to the [examples](examples).

