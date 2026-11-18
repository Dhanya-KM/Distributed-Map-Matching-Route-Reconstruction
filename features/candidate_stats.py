"""Role A, step 2: choose the candidate search radius R using data.

For each radius R we measure
  * miss rate      : % of GPS points whose reference (nearest route) arc is farther than R
  * mean candidates: average number of arcs within R of a GPS point
(bigger R -> fewer misses, but more wrong candidates for the classifier to reject)

Run from repo root:
    python -m features.candidate_stats            (10 train trips, quick)
    python -m features.candidate_stats all        (all 80 train trips, slower)
Output: results/candidate_stats.csv
"""
import sys

import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

from data_processing.loader import list_trips, load_trip
from features.explore_noise import project_trip, build_arc_lines

RADII = [10, 15, 20, 30, 50, 75, 100]


def trip_stats(d):
    gps_xy, node_xy = project_trip(d)
    lines = build_arc_lines(d["arcs"], node_xy)
    pts = shapely.points(gps_xy)

    # distance from every GPS point to the reference route (nearest route arc)
    route_union = shapely.MultiLineString([lines[a] for a in d["route"]])
    dist_route = shapely.distance(pts, route_union)

    # how many arcs lie within R of each point?
    tree = STRtree(lines)
    out = {}
    for R in RADII:
        pairs = tree.query(pts, predicate="dwithin", distance=R)  # shape (2, n_pairs)
        n_cand = np.bincount(pairs[0], minlength=len(pts))
        out[R] = (float((dist_route > R).sum()), float(n_cand.sum()), len(pts),
                  float((n_cand == 0).sum()))
    return out


if __name__ == "__main__":
    trips = list_trips("train") if (len(sys.argv) > 1 and sys.argv[1] == "all") else list_trips("train")[:10]
    tot = {R: np.zeros(4) for R in RADII}
    for t in trips:
        d = load_trip(t)
        for R, v in trip_stats(d).items():
            tot[R] += np.array(v)
        print("done", d["id"], flush=True)

    rows = []
    for R, (miss, cands, n, empty) in tot.items():
        rows.append({"R_m": R, "miss_rate_%": 100 * miss / n,
                     "mean_candidates_per_point": cands / n,
                     "points_with_no_candidate_%": 100 * empty / n, "n_points": int(n)})
    df = pd.DataFrame(rows).round(2)
    df.to_csv("results/candidate_stats.csv", index=False)
    print(df.to_string(index=False))
