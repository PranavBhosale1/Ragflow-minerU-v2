import json
import networkx as nx
from typing import Any, Dict, List, Optional, Tuple


def _escape_mermaid_label(text: str) -> str:
    return text.replace("\n", " ").replace('"', "&#34;").strip()


def node_label(attrs: dict, node_id: Any) -> str:
    label = attrs.get("text") or attrs.get("type") or f"Node {node_id}"
    return _escape_mermaid_label(str(label))


def _node_mermaid_definition(node_id: int, attrs: dict) -> str:
    label = node_label(attrs, node_id)
    shape_type = attrs.get("type", "process")

    mermaid_id = f"n{node_id}"
    if shape_type == "decision":
        return f"    {mermaid_id}{{\"{label}\"}}"
    return f"    {mermaid_id}[\"{label}\"]"


def export_graph(G: nx.DiGraph, path: str = "flowchart.mmd") -> None:
    lines = ["flowchart TD"]

    for node_id in G.nodes:
        lines.append(_node_mermaid_definition(node_id, dict(G.nodes[node_id])))

    for src, dst in G.edges:
        lines.append(f"    n{src} --> n{dst}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def export_rag_markdown(
    G: nx.DiGraph,
    path: str,
    *,
    source_hint: Optional[str] = None,
) -> None:
    """Plain-language text for embedding: nodes and edges as retrievable lines."""
    lines: List[str] = [
        "# Flowchart extraction (RAG layer)",
        "",
        "This block summarizes an extracted flowchart as structured facts for search.",
    ]
    if source_hint:
        lines.extend(["", f"Source: {source_hint}", ""])
    else:
        lines.append("")

    lines.extend(["## Nodes", ""])
    for node_id in sorted(G.nodes):
        attrs = dict(G.nodes[node_id])
        ntype = attrs.get("type", "process")
        label = node_label(attrs, node_id)
        lines.append(f"- Node {node_id} ({ntype}): {label}")

    lines.extend(["", "## Edges (directed)", ""])
    for src, dst in G.edges:
        a = dict(G.nodes[src])
        b = dict(G.nodes[dst])
        la = node_label(a, src)
        lb = node_label(b, dst)
        lines.append(f"- From node {src} ({la}) to node {dst} ({lb}).")

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"The flowchart contains {n_nodes} node(s) and {n_edges} directed edge(s).",
            "",
        ]
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _bbox_to_list(bbox: Any) -> Optional[List[int]]:
    if bbox is None:
        return None
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return [int(x) for x in bbox]
    return None


def export_graph_json(G: nx.DiGraph, path: str) -> None:
    """Structured graph for tools; aligns with optional bbox/search_area on nodes."""
    nodes_out: List[Dict[str, Any]] = []
    for node_id in sorted(G.nodes):
        attrs = dict(G.nodes[node_id])
        nid = int(node_id) if isinstance(node_id, (int, float)) else node_id
        entry: Dict[str, Any] = {
            "id": nid,
            "type": attrs.get("type", "process"),
            "text": attrs.get("text") or "",
        }
        bbox = _bbox_to_list(attrs.get("bbox"))
        if bbox is not None:
            entry["bbox"] = bbox
        sa = _bbox_to_list(attrs.get("search_area"))
        if sa is not None:
            entry["search_area"] = sa
        nodes_out.append(entry)

    edges_out = [{"from": int(u), "to": int(v)} for u, v in G.edges]

    payload = {"nodes": nodes_out, "edges": edges_out}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
