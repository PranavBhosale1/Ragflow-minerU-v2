# Flowchart extraction (RAG layer)

This block summarizes an extracted flowchart as structured facts for search.

Source: C:\Users\Pranav\Desktop\Ragflow-minerU-v2\vit-test\Cooler_pipe_flowchart.pdf

## Nodes

- Node 0 (process): Std Steel 0011 1331 95
- Node 1 (process): Drains
- Node 2 (process): CC
- Node 3 (process): Hose assembly
- Node 4 (process): Oil
- Node 5 (decision): Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14
- Node 6 (process): Std Steel 0011 1331 95
- Node 7 (process): Rubber
- Node 8 (process): Coolant
- Node 9 (process): BB
- Node 10 (process): Hose assembly
- Node 11 (decision): Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14
- Node 12 (process): No
- Node 13 (decision): Alu steel> 050 0011 9054 95 Std Steel> 050 0011 1331 95
- Node 14 (process): Alu steel = No after treatment Std Steel = paint 9822 0976 14
- Node 15 (process): Cooler pipe
- Node 16 (process): Use Welds?
- Node 17 (process): BB
- Node 18 (process): Yes (Outside)
- Node 19 (process): Air
- Node 20 (process): Before the cooler
- Node 21 (process): Alu steel= Alu paint 9822 0503 02 Std Steel = 9822 0976 14 paint
- Node 22 (process): No
- Node 23 (process): Use Welds?
- Node 24 (process): Alu steel 00119054 95
- Node 25 (process): No After treatment
- Node 26 (process): Yes (Outside)
- Node 27 (process): BB
- Node 28 (process): Alu steel 0011 9054 95
- Node 29 (process): No
- Node 30 (process): Alu steel paint 9822 0503 02 (Outside)
- Node 31 (process): Use Welds?
- Node 32 (process): After the cooler
- Node 33 (process): Alu steel 0011 9054 95
- Node 34 (process): AA
- Node 35 (process): No After treatment
- Node 36 (process): Yes
- Node 37 (process): RVS 0011 9510 60

## Edges (directed)

- From node 0 (Std Steel 0011 1331 95) to node 5 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14).
- From node 1 (Drains) to node 3 (Hose assembly).
- From node 1 (Drains) to node 0 (Std Steel 0011 1331 95).
- From node 3 (Hose assembly) to node 5 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14).
- From node 3 (Hose assembly) to node 0 (Std Steel 0011 1331 95).
- From node 4 (Oil) to node 10 (Hose assembly).
- From node 4 (Oil) to node 6 (Std Steel 0011 1331 95).
- From node 4 (Oil) to node 1 (Drains).
- From node 5 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14) to node 2 (CC).
- From node 6 (Std Steel 0011 1331 95) to node 11 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14).
- From node 8 (Coolant) to node 13 (Alu steel> 050 0011 9054 95 Std Steel> 050 0011 1331 95).
- From node 8 (Coolant) to node 1 (Drains).
- From node 8 (Coolant) to node 4 (Oil).
- From node 8 (Coolant) to node 7 (Rubber).
- From node 10 (Hose assembly) to node 6 (Std Steel 0011 1331 95).
- From node 10 (Hose assembly) to node 11 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14).
- From node 11 (Galvanizing FelZn 12pF4 AC Std 6767k OR Painting 9822 0976 14) to node 9 (BB).
- From node 12 (No) to node 14 (Alu steel = No after treatment Std Steel = paint 9822 0976 14).
- From node 13 (Alu steel> 050 0011 9054 95 Std Steel> 050 0011 1331 95) to node 16 (Use Welds?).
- From node 14 (Alu steel = No after treatment Std Steel = paint 9822 0976 14) to node 17 (BB).
- From node 15 (Cooler pipe) to node 19 (Air).
- From node 15 (Cooler pipe) to node 1 (Drains).
- From node 15 (Cooler pipe) to node 4 (Oil).
- From node 15 (Cooler pipe) to node 8 (Coolant).
- From node 16 (Use Welds?) to node 18 (Yes (Outside)).
- From node 16 (Use Welds?) to node 12 (No).
- From node 18 (Yes (Outside)) to node 21 (Alu steel= Alu paint 9822 0503 02 Std Steel = 9822 0976 14 paint).
- From node 19 (Air) to node 20 (Before the cooler).
- From node 20 (Before the cooler) to node 23 (Use Welds?).
- From node 21 (Alu steel= Alu paint 9822 0503 02 Std Steel = 9822 0976 14 paint) to node 17 (BB).
- From node 22 (No) to node 24 (Alu steel 00119054 95).
- From node 23 (Use Welds?) to node 26 (Yes (Outside)).
- From node 23 (Use Welds?) to node 22 (No).
- From node 24 (Alu steel 00119054 95) to node 25 (No After treatment).
- From node 25 (No After treatment) to node 27 (BB).
- From node 26 (Yes (Outside)) to node 28 (Alu steel 0011 9054 95).
- From node 28 (Alu steel 0011 9054 95) to node 30 (Alu steel paint 9822 0503 02 (Outside)).
- From node 29 (No) to node 33 (Alu steel 0011 9054 95).
- From node 30 (Alu steel paint 9822 0503 02 (Outside)) to node 27 (BB).
- From node 30 (Alu steel paint 9822 0503 02 (Outside)) to node 25 (No After treatment).
- From node 31 (Use Welds?) to node 36 (Yes).
- From node 31 (Use Welds?) to node 29 (No).
- From node 32 (After the cooler) to node 31 (Use Welds?).
- From node 32 (After the cooler) to node 19 (Air).
- From node 33 (Alu steel 0011 9054 95) to node 35 (No After treatment).
- From node 35 (No After treatment) to node 34 (AA).
- From node 36 (Yes) to node 37 (RVS 0011 9510 60).
- From node 37 (RVS 0011 9510 60) to node 35 (No After treatment).
- From node 37 (RVS 0011 9510 60) to node 33 (Alu steel 0011 9054 95).

## Summary

The flowchart contains 38 node(s) and 49 directed edge(s).

