# Python PubSub
A simple python implementation of a message router with many subscribers and many publishers.

It can be considered as as fork of the project: [CoreMQ](https://github.com/deejross/coremq).

<center>
<div><a href='//sketchviz.com/@philipperemy/8f597379f217ca0b6a20700ebc7f0b22'><img src='https://sketchviz.com/@philipperemy/8f597379f217ca0b6a20700ebc7f0b22/765f0d983410a72083cd967e7e0535dee8f9bcfc.sketchy.png' style='max-width: 100%;'></a><br/><span style='font-size: 80%;color:#555;'>Hosted on <a href='//sketchviz.com/' style='color:#555;'>Sketchviz</a></span></div>
</center>

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


## Misc

Visualization provided by https://sketchviz.com/.

```
# http://www.graphviz.org/content/cluster

digraph G {
  graph [fontname = "Handlee"];
  node [fontname = "Handlee"];
  edge [fontname = "Handlee"];

  bgcolor=transparent;

  subgraph cluster_0 {
    style=filled;
    color=lightgrey;
    node [style=filled,color=pink];
    "publisher 1" -> "broker"[label="publish to c1"]
    "publisher 1" -> "broker"[label="publish to  c2"]
    "publisher 2" -> "broker"[label="publish to  c1"]
    "publisher 3" -> "broker"[label="publish to  c2"]
    "subscriber 1" -> "broker"[label="subscribe to c1"]
    "subscriber 2" -> "broker"[label="subscribe to c2"]
    "broker" -> "subscriber 1"[label=""]
    "broker" -> "subscriber 2"[label=""]
    
    label = "*Publisher / Subscriber broker*";
    fontsize = 20;
  }

  broker [shape=Mdiamond];
}
```
