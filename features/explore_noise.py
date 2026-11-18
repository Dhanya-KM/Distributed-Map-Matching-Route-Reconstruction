"""Role A, step 1: how far are GPS points from the reference route?

Run from repo root:
    python -m features.explore_noise                (uses a few default trips)
    python -m features.explore_noise train 00000005 (one trip)

Output: results/noise_distances.csv and a printed table of percentiles.
"""
import sys

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import LineString

from data_processing.loader import DATA_ROOT, list_trips, load_trip

# IMPORTANT: trips are located in DIFFERENT places (longitudes from about 8E to 37E),
# so we cannot use one fixed UTM zone. We pick the UTM zone from each trip's own centre.
def metric_transformer(lon_mean, lat_mean):
    zone = int((lon_mean + 180) // 6) + 1
    epsg = (32600 if lat_mean >= 0 else 32700) + zone   # 326xx = north, 327xx = south
    return Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)  # order: lon, lat


def project_trip(d):
    """Return GPS points (n,2) and node coordinates (m,2) in metres."""
    tr = d["track"]
    to_metric = metric_transformer(tr.lon.mean(), tr.lat.mean())
    gx, gy = to_metric.transform(tr.lon.to_numpy(), tr.lat.to_numpy())
    nx, ny = to_metric.transform(d["nodes"].lon.to_numpy(), d["nodes"].lat.to_numpy())
    return np.column_stack([gx, gy]), np.column_stack([nx, ny])


def build_arc_lines(arcs, node_xy):
    """One LineString per arc (index = arc_id)."""
    a = arcs[["from_node", "to_node"]].to_numpy()
    return [LineString([node_xy[f], node_xy[t]]) for f, t in a]


def distance_to_route(d):
    """Distance (metres) from each GPS point to the NEAREST arc of the reference route."""
    gps_xy, node_xy = project_trip(d)
    lines = build_arc_lines(d["arcs"], node_xy)
    route_lines = shapely.MultiLineString([lines[a] for a in d["route"]])
    pts = shapely.points(gps_xy)
    return shapely.distance(pts, route_lines)


def check_extent(d):
    tr = d["track"]
    return tr.lon.min(), tr.lon.max(), tr.lat.min(), tr.lat.max()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        trips = [DATA_ROOT / sys.argv[1] / sys.argv[2]]
    else:
        trips = list_trips("train")[:10] + list_trips("student_test")

    rows = []
    for t in trips:
        d = load_trip(t)
        dist = distance_to_route(d)
        lon0, lon1, lat0, lat1 = check_extent(d)
        rows.append({
            "trip": d["id"], "zone_epsg": metric_transformer(d["track"].lon.mean(), d["track"].lat.mean()).target_crs.to_epsg(), "n_points": len(dist),
            "lon_range": f"{lon0:.3f}..{lon1:.3f}", "lat_range": f"{lat0:.3f}..{lat1:.3f}",
            "median_m": np.median(dist), "p90_m": np.percentile(dist, 90),
            "p95_m": np.percentile(dist, 95), "p99_m": np.percentile(dist, 99),
            "max_m": dist.max(),
        })
    out = pd.DataFrame(rows).round(1)
    out.to_csv("results/noise_distances.csv", index=False)
    print(out.to_string(index=False))
