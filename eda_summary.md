# PathSnap: EDA Summary (reference for the team)

Source: output of `python -m data_processing.eda` on the provided dataset.
Full per-trip numbers are in `results/eda_inventory.csv`.
Use this file as a reference, then write your own notes and report text in your own words.

---

## 1. Dataset inventory

| Partition | Trips |
|---|---|
| train | 80 |
| student_test | 10 |
| evaluator test | 10 (hidden, final evaluation only) |

Each trip has 4 raw files (whitespace-separated, no headers):

| File | Columns | Meaning |
|---|---|---|
| `.track` | lon, lat, time (s) | Noisy GPS observations, nominally 1 Hz |
| `.nodes` | lon, lat | Road-network nodes (row index = node_id) |
| `.arcs` | from_node, to_node | Directed road segments (row index = arc_id) |
| `.route` | arc_id | Reference route: ordered arc_ids the vehicle travelled |

---

## 2. Size statistics

| Quantity | Partition | Min | Median | Mean | Max |
|---|---|---|---|---|---|
| GPS points per trip | train | 361 | 1,529 | 2,605 | 19,313 |
| GPS points per trip | student_test | 262 | 1,420 | 1,916 | 3,958 |
| Network nodes | train | 299 | 9,608 | 24,169 | 155,003 |
| Network nodes | student_test | 1,770 | 6,597 | 9,069 | 26,635 |
| Network arcs | train | 649 | 19,527 | 48,461 | 307,392 |
| Network arcs | student_test | 3,577 | 13,145 | 18,504 | 56,027 |
| Reference route length (arcs) | train | 59 | 280 | 392 | 2,266 |
| Reference route length (arcs) | student_test | 95 | 250 | 348 | 1,323 |

---

## 3. Data-quality findings

| Check | Result |
|---|---|
| Missing values in `.track` | 0 trips affected |
| Trips with a time gap larger than 1 s | **66 of 90** |
| Average share of steps exactly 1 s apart | about 94% (lowest trip about 53%) |
| Largest gaps | trip 90 (about 153,000 s), trip 78 (about 52,800 s); a few others in the 600 to 2,700 s range |
| Reference route not fully connected | **11 of 90** trips (10 train, 1 student_test); these are 98.1% to 99.9% connected |
| Road network with more than one connected component | **89 of 90** trips |
| Isolated nodes | 0 |
| Route arc IDs valid (inside arcs file) | all trips |

---

## 4. What this means for our design (check each point yourselves)

1. **Per-trip road networks.** Network size varies enormously between trips (299 to 155,003 nodes), so each trip appears to come with its own network. Arc IDs are then **not comparable across trips**, so we cannot classify "which arc ID". We classify **(GPS point, candidate arc) pairs** as correct / not correct.
   *To verify:* compare the node coordinates of two trips in the same area.
2. **Large networks need a spatial index.** Up to about 307k arcs per trip. Brute-force distance to every arc will be too slow. Use a KD-tree or STRtree.
3. **Time gaps must be handled.** Most steps are 1 s, but a few huge gaps exist. The HMM needs a rule for gaps (for example, break the sequence or relax the transition model).
4. **Reference route is not perfect.** 11 trips contain small breaks. Treat the route as reference information, not perfect truth, and mention this as a limitation in the report.
5. **Fragmented networks.** Many components means a candidate on a different component may be unreachable. Transition logic must allow for this.
6. **Use metres, not degrees.** Coordinates are lon, lat (first column is longitude). Project to a metric CRS before computing distances, and justify the choice in the report.
7. **No missing values**, so no imputation is needed. State this in the report's missing-value analysis.

---

## 5. Questions to answer in your own words (`results/eda_notes.md`)

- What does each of the 4 file types represent, and how do they relate?
- On the maps of trips 5, 90 and 78, how far do the blue GPS dots drift from the green route?
- What looks different in trips 90 and 78?
- Why can't we use degrees for distance?
- Which trips are anomalous, and what will we do with them?

Dhanya's observations from the maps (fill in):

- Trip 00000005:
- Trip 00000090:
- Trip 00000078:

---

## 6. Next step

Candidate generation and labelling (Role A):
1. Project coordinates to metres.
2. Build a spatial index of arcs per trip.
3. For each GPS point, find candidate arcs within a radius R.
4. Label each candidate 1 if it is the correct route arc, otherwise 0.
5. Report the **candidate miss rate** (share of points where the correct arc is not among the candidates).
