# PathSnap: EDA Notes (Role A)

---

## 1. The four file types and how they relate

Each trip folder consists of four whitespace-separated, headerless files that define the spatial tracking data and the topological road network:

- **`.track` (GPS Observations):** A chronological sequence of raw GPS measurements recorded as `(longitude, latitude, timestamp)`. Recorded nominally at 1 Hz, these coordinates contain real-world measurement noise, satellite drift, and multipath distortions in dense urban canyons.
- **`.nodes` (Network Intersections & Endpoints):** The spatial vertices of the digital road network defined by `(longitude, latitude)`. The 0-indexed line number serves as the unique `node_id`. Nodes represent physical road junctions, intersections, and segment terminals.
- **`.arcs` (Road Segments / Edges):** The directed links connecting two nodes `(from_node_id, to_node_id)`. The 0-indexed line number serves as the unique `arc_id`.
- **`.route` (Reference Ground-Truth Sequence):** The ordered list of `arc_id`s representing the sequence of road segments the vehicle actually traveled. Consecutive arcs in a valid route connect topologically such that `arcs[i].to_node == arcs[i+1].from_node`.

**Network Structure & Route Purpose:**  
Together, **`.nodes` and `.arcs` define the directed road network graph $G = (V, E)$** on which vehicles are physically constrained to travel. The **`.route` serves as reference supervisory information** used to label candidate segments during training and evaluate reconstruction fidelity. Importantly, the reference route is not infallible ground truth—several trips have slight topological breaks, and in some trips (e.g., Trip 2), GPS recording continued well after the annotated route ended.

---

## 2. What the maps show

- **Trip 00000005 (clean case):**  
  The raw GPS track cleanly hugs the green reference route along a continuous highway and urban corridor with minimal lateral scatter. The median GPS drift is only ~4.5 m, demonstrating nominal 1 Hz sensor behavior with unbroken road alignment and no major parallel road confusion.
- **Trip 00000002, top-left end (GPS continues past the green route):**  
  At the northwest terminus, the green reference route abruptly ends while the raw blue GPS points continue streaming onward for several kilometers through the road network. This represents an unannotated trajectory tail where valid GPS points exist without corresponding ground-truth route labels.
- **Trip 00000002, loop/wiggle near the bottom right:**  
  Near the southeastern end, the vehicle executes a complex turnaround loop involving sharp directional changes and close parallel road segments. The GPS noise cloud visibly overlaps multiple adjacent candidate arcs, creating high local ambiguity that pure nearest-neighbor snapping fails to resolve without heading and connectivity constraints.
- **Trip 00000090 (time gap of about 153,000 s):**  
  A massive temporal pause of ~42.5 hours occurs between consecutive GPS observations mid-trip (indicating the vehicle was parked, powered off over a weekend, or logging halted). Time cannot be treated as uniformly continuous across this interval, requiring the transition model to reset rather than penalizing network distance.
- **Trip 00000078 (time gap of about 52,800 s):**  
  This trip contains an overnight temporal gap of ~14.7 hours where logging paused and resumed at a nearby location. Standard vehicle speed assumptions break down across this break, necessitating a transition gap-handling policy.

---

## 3. Coordinates and distance

**Why distance cannot be measured in degrees:**  
Degrees of latitude and longitude represent angular coordinates on the Earth's ellipsoidal surface rather than fixed linear units of metric distance. While $1^\circ$ of latitude corresponds to approximately 111 km everywhere, $1^\circ$ of longitude scales with the cosine of latitude: at the equator $1^\circ \approx 111.3\text{ km}$, but at $56^\circ\text{N}$ (e.g., Moscow / Trip 3), $1^\circ \text{ lon} \approx 62.3\text{ km}$. Calculating Euclidean distances directly on raw $(\Delta\text{lon}, \Delta\text{lat})$ creates non-isotropic distortion, compressing east-west distances and completely falsifying perpendicular distance calculations to candidate road segments.

**Projection choice & per-trip UTM zone selection:**  
We project all geographic coordinates to planar metric coordinates using the **Universal Transverse Mercator (UTM / WGS84)** projection system. The UTM zone (and corresponding EPSG code, e.g., EPSG 32632 for Germany, EPSG 32616 for Alabama, USA, EPSG 32637/32640 for Russia) must be determined **dynamically per trip** based on the trip's central longitude ($\text{Zone} = \lfloor(\text{lon} + 180)/6\rfloor + 1$). The dataset contains trajectories collected in widely separated regions around the world (as confirmed by the `lon_range` column in `results/noise_distances.csv`). A single fixed UTM zone would introduce extreme projection distortion for trips located thousands of kilometers away from the central meridian.

---

## 4. How far is the GPS from the reference route?

*Extracted from `results/noise_distances.csv`:*

| Quantity | Value (typical trip, e.g. Trip 1 / 5) | Value (Trip 2) |
|---|---|---|
| Median distance (m) | **4.3 – 4.5 m** | **5.7 m** |
| 95th percentile (m) | **12.4 – 13.2 m** | **242.4 m** |
| 99th percentile (m) | **15.7 – 20.8 m** | **481.6 m** |
| Maximum (m) | **27.0 – 27.2 m** | **569.7 m** |

**Interpretation of GPS noise & why Trip 2 is anomalous:**  
For typical trips, GPS error is modest and tightly bound: over 50% of readings lie within 4.5 m of the true road center, and 95% of readings fall within 13 m, with maximum outlier spikes rarely exceeding 30 m. This confirms that sensor measurement noise is well-characterized by a zero-mean Gaussian distribution with $\sigma \approx 5\text{–}8\text{ m}$.  
**Trip 2 is an extreme anomaly** because the GPS trajectory continues for kilometers after the annotated reference route stops. Measuring the distance from those subsequent GPS points back to the truncated reference route yields artificial distances of hundreds of meters (up to 569.7 m), skewing global noise statistics unless isolated.

---

## 5. Data-quality issues and what we do about each

| Issue | Evidence (from `eda_inventory.csv`) | Our decision |
|---|---|---|
| **Time gaps** | 66 of 90 trips contain gaps $> 1\text{ s}$ (max 153,000 s in Trip 90; 52,800 s in Trip 78). | When $\Delta t > 60\text{ s}$, split the trajectory or reset HMM state transition probabilities so temporal/network penalties are not applied across multi-hour pauses. |
| **Reference route not fully connected** | 11 of 90 trips contain minor discontinuities (98.1% to 99.9% connected). | Treat reference routes as supervisory training guides rather than infallible truth; use Dijkstra shortest-path stitching to guarantee 100% connectivity in our output. |
| **Fragmented road networks** | 89 of 90 trips have $>1$ connected component in their road graph. | Prune unreachable disconnected graph fragments or assign zero transition probability across unreachable components to avoid path routing failures. |
| **Very large networks** | Trajectory networks reach up to 155,003 nodes and 307,392 arcs (Trip 43). | Brute-force distance search is unfeasible ($O(N \cdot M)$); implement spatial indexing (KD-Tree / R-Tree) to retrieve candidate arcs in $O(\log M)$ time. |
| **Missing values** | 0 trips affected (0 missing values across all `.track` coordinates and timestamps). | No imputation required; add input schema assertion checks in data loader to ensure continuous integrity. |
| **Trip 2: GPS continues past reference route** | 95th percentile error is 242.4 m; maximum distance reaches 569.7 m. | Truncate Trip 2 candidate evaluation and training pairs to the time window of the reference route so unannotated points do not pollute training labels. |

---

## 6. Do trips share road networks?

**Evidence:**  
Each trip contains its own isolated `.nodes` and `.arcs` files. Across trips, the number of nodes varies drastically from 299 to 155,003, and the coordinate bounding boxes span completely different countries and continents (Germany, Central Asia, Russia, North America). For instance, arc ID 500 in Trip 1 designates a local street in Darmstadt, Germany, whereas arc ID 500 in Trip 8 designates a segment in Alabama, USA. There is no shared global arc index.

**Impact on ML Problem Formulation:**  
Because arc IDs have no common meaning across trips, we cannot frame the problem as multi-class classification over arc IDs. Instead, the problem must be structured as **relational pairwise binary classification**:
- Each tabular dataset row represents a `(GPS point, candidate road segment)` pair.
- The features are coordinate-invariant spatial-temporal relationships: orthogonal distance, heading difference ($\Delta \theta$), speed consistency ($\Delta d / \Delta t$), and road connectivity degree.
- The target label is binary: $y=1$ if the candidate segment is the true road segment, and $y=0$ if it is an incorrect candidate or distractor.

---

## 7. Choosing the search radius R

*Summary of candidate extraction over all 208,417 GPS points in the 80 train trips:*

| R (m) | Miss rate (%) | Mean candidates per point | Points with no candidate (%) |
|:---:|:---:|:---:|:---:|
| 10 | 27.43 | 2.03 | 22.59 |
| 15 | 17.20 | 2.85 | 13.62 |
| 20 | 14.11 | 3.64 | 11.18 |
| 30 | 12.18 | 5.27 | 9.73 |
| 50 | 10.83 | 8.96 | 8.75 |
| 75 | 9.99 | 14.84 | 6.53 |
| 100 | 9.59 | 22.36 | 0.68 |

- **Our chosen R:**  
  **$R = 30\text{ m}$ (with $R = 50\text{ m}$ as dynamic fallback)**.
- **Why this value (trade-off between misses and number of candidates):**  
  At $R \le 20\text{ m}$, the miss rate is unacceptable ($14.11\%$ to $27.43\%$), meaning the true road segment is missing from the candidate pool over one-seventh of the time.  
  Moving from $R=30\text{ m}$ to $R=100\text{ m}$ offers diminishing returns: the miss rate drops by only $2.59\%$ (from $12.18\%$ to $9.59\%$), while the average candidate pool quadruples from 5.27 to 22.36 candidates per point. In Viterbi decoding, the transition computation scales quadratically ($K^2$): evaluating 22.36 candidates requires computing $\approx 500$ Dijkstra network paths per step compared to only $\approx 28$ paths at $R=30\text{ m}$—a **$18\times$ computational overhead** for a marginal $2.5\%$ recall gain.
- **What causes any remaining miss rate:**  
  The stubborn ~9.6% residual miss rate across all radii is overwhelmingly driven by **Trip 2's unannotated tail** (where valid GPS observations travel far beyond the ended reference route) and occasional GPS outliers during severe satellite signal loss.
- **Our decision on Trip 2 and why:**  
  For training and candidate metric benchmarking, we clip Trip 2 to the reference route's temporal window. In production inference on test data where reference routes are absent, points with 0 candidates within $R=30\text{ m}$ trigger a fallback nearest-arc query to prevent empty trellis steps.

---

## 8. Open questions for the team

1. **Time gap transition policy:** When a temporal gap exceeds $\Delta t > 60\text{ s}$ (as in Trips 90 and 78), should we split the Viterbi trellis into independent sub-trajectories, or simply flatten the transition matrix to uniform probabilities?
2. **Empty candidate handling:** When a GPS point has 0 candidate arcs within $R=30\text{ m}$ (e.g. sharp bridges or tunnels), should we interpolate the position, or expand radius $R$ to the nearest 1–2 arcs?
3. **Graph routing edge costs:** In Dijkstra path stitching between non-consecutive matched arcs, should edge weights be pure Euclidean arc lengths (meters) or estimated travel time based on road classification?
