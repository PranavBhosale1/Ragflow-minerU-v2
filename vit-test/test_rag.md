# Flowchart extraction (RAG layer)

This block summarizes an extracted flowchart as structured facts for search.

Source: C:\Users\Pranav\Desktop\Ragflow-minerU-v2\vit-test\Air_inlet_flowchart.pdf

## Nodes

- Node 0 (decision): Metal: ~Std Steel ~Alu Steel
- Node 1 (process): BB
- Node 2 (process): No after-treatment
- Node 3 (process): No
- Node 4 (process): Alu Steel 00119054 95
- Node 5 (process): Use Welds?
- Node 6 (decision): Air Inlet
- Node 7 (decision): AA
- Node 8 (process): Yes
- Node 9 (process): STD Steel 00119039 55
- Node 10 (process): Nickelled (25 um) or KTL
- Node 11 (process): Plastic

## Edges (directed)

- From node 0 (Metal: ~Std Steel ~Alu Steel) to node 5 (Use Welds?).
- From node 2 (No after-treatment) to node 1 (BB).
- From node 3 (No) to node 4 (Alu Steel 00119054 95).
- From node 4 (Alu Steel 00119054 95) to node 2 (No after-treatment).
- From node 5 (Use Welds?) to node 8 (Yes).
- From node 5 (Use Welds?) to node 3 (No).
- From node 6 (Air Inlet) to node 11 (Plastic).
- From node 6 (Air Inlet) to node 0 (Metal: ~Std Steel ~Alu Steel).
- From node 8 (Yes) to node 9 (STD Steel 00119039 55).
- From node 9 (STD Steel 00119039 55) to node 10 (Nickelled (25 um) or KTL).
- From node 10 (Nickelled (25 um) or KTL) to node 7 (AA).

## Summary

The flowchart contains 12 node(s) and 11 directed edge(s).

