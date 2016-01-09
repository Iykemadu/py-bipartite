#### Introduction ####

This is a python implementation of a network topology generator. This generator relies on a bipartite graph structure: one level is for L2 devices (typically Ethernet switches) and the other level is for L3 devices (e.g. routers). The generator picks the degree of L2 and L3 nodes from two separate power-law distributions (Pareto distributions are used). The bipartite graph can be projected on the L3 set to produce a pure L3 network.

Here is an example invocation and the resulting graphs.

```
  python bipartite.py generate:30:2:2:50:-1:1 plot:bipartite.png project giant plot:projected.png
```

#### Bipartite graph (L2 nodes in blue ; L3 nodes in green) ####

![https://py-bipartite.googlecode.com/svn/resources/bipartite.png](https://py-bipartite.googlecode.com/svn/resources/bipartite.png)

#### L3-projected graph (only the largest connected component) ####

![https://py-bipartite.googlecode.com/svn/resources/projected.png](https://py-bipartite.googlecode.com/svn/resources/projected.png)