import networkx as nx
from typing import List, Dict


def build_graph(nodes: List[Dict], edges: List[Dict], verbose: bool = True) -> nx.DiGraph:
    """
    Construct NetworkX graph from detected nodes and pre-calculated edge connections.
    """
    G = nx.DiGraph()

    # Add Nodes
    for i, node in enumerate(nodes):
        # copy node data
        G.add_node(i, **{k: v for k, v in node.items()})

    # Add Edges
    edges_added = 0
    for edge in edges:
        u, v = edge['src'], edge['dst']

        # Avoid duplicate edges
        if not G.has_edge(u, v):
            G.add_edge(u, v)
            edges_added += 1

    if verbose:
        print(f"Graph built: {len(nodes)} nodes, {edges_added} edges")

    # Graph-level correction: attempt to reduce cycles by reversing edges when helpful
    try:
        cycles_before = list(nx.simple_cycles(G))
        if cycles_before:
            # For each edge, try reversing it if it reduces number of cycles
            changed = True
            # Small iterative pass
            for (u, v) in list(G.edges()):
                # try reversing
                G.remove_edge(u, v)
                if not G.has_edge(v, u):
                    G.add_edge(v, u)
                    cycles_after = list(nx.simple_cycles(G))
                    if len(cycles_after) > len(cycles_before):
                        # revert
                        G.remove_edge(v, u)
                        G.add_edge(u, v)
                    else:
                        cycles_before = cycles_after
                else:
                    # revert if parallel exists
                    G.add_edge(u, v)
    except Exception:
        pass

    return G
