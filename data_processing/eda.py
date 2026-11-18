"""Step 2: dataset inventory + data-quality checks for train and student_test.

Run from the repo root:  python -m data_processing.eda
Outputs: results/eda_inventory.csv and results/eda_*.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from data_processing.loader import list_trips, load_trip


def summarise(partition, trip_dir):
    d = load_trip(trip_dir)
    tr, nodes, arcs, route = d["track"], d["nodes"], d["arcs"], d["route"]
    dt = np.diff(tr["t"].to_numpy())
    n = len(nodes)

    # network connectivity (treat arcs as undirected just to count components)
    g = coo_matrix((np.ones(len(arcs)), (arcs.from_node, arcs.to_node)), shape=(n, n))
    n_comp, _ = connected_components(g, directed=False)
    used = np.zeros(n, bool)
    used[arcs.from_node] = True
    used[arcs.to_node] = True

    # is the reference route a connected chain? arc[i].to == arc[i+1].from
    if route is not None and len(route) > 1:
        a = arcs.to_numpy()
        frac_conn = float(np.mean(a[route[:-1], 1] == a[route[1:], 0]))
    else:
        frac_conn = np.nan

    return {
        "partition": partition, "trip": d["id"],
        "n_points": len(tr),
        "n_missing": int(tr.isna().sum().sum()),
        "t_sorted": bool((dt > 0).all()),
        "pct_dt_1s": float((dt == 1).mean() * 100),
        "max_gap_s": float(dt.max()),
        "lon_min": tr.lon.min(), "lon_max": tr.lon.max(),
        "lat_min": tr.lat.min(), "lat_max": tr.lat.max(),
        "n_nodes": n, "n_arcs": len(arcs),
        "isolated_nodes": int((~used).sum()),
        "components": int(n_comp),
        "route_len": 0 if route is None else len(route),
        "route_connected_frac": frac_conn,
        "route_arc_id_valid": bool(route is not None and route.max() < len(arcs)),
    }


def main():
    rows = []
    for part in ["train", "student_test"]:
        for t in list_trips(part):
            rows.append(summarise(part, t))
    df = pd.DataFrame(rows)
    df.to_csv("results/eda_inventory.csv", index=False)

    print(df.groupby("partition")[["n_points", "n_nodes", "n_arcs", "route_len"]].describe().T)
    print("\nTrips per partition:\n", df.partition.value_counts())
    print("\nTrips with gaps > 1 s max:", (df.max_gap_s > 1).sum())
    print("Trips with missing values:", (df.n_missing > 0).sum())
    print("Trips where route is not fully connected:", (df.route_connected_frac < 1).sum())
    print("Trips with >1 network component:", (df.components > 1).sum())

    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    df.n_points.hist(ax=ax[0], bins=20); ax[0].set_title("GPS points per trip")
    df.n_arcs.hist(ax=ax[1], bins=20); ax[1].set_title("Arcs per trip network")
    df.max_gap_s.hist(ax=ax[2], bins=20); ax[2].set_title("Max time gap (s) per trip")
    plt.tight_layout(); plt.savefig("results/eda_distributions.png", dpi=150)


if __name__ == "__main__":
    main()
