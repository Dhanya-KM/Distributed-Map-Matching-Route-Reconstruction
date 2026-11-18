"""Load raw PathSnap trips.

Each trip folder contains four whitespace-separated files without headers:
  .track  -> lon, lat, time_s
  .nodes  -> lon, lat            (row index = node_id)
  .arcs   -> from_node, to_node  (row index = arc_id)
  .route  -> arc_id              (reference route, in order)
"""
import os
from pathlib import Path

import pandas as pd

# Change this path, or set the environment variable PATHSNAP_DATA
DATA_ROOT = Path(os.environ.get("PATHSNAP_DATA", "Student folder"))


def list_trips(partition):
    """partition: 'train' or 'student_test'. Returns sorted list of trip folders."""
    return sorted(p for p in (DATA_ROOT / partition).iterdir() if p.is_dir())


def _read(path, names, dtype=None):
    return pd.read_csv(path, sep=r"\s+", header=None, names=names, dtype=dtype)


def load_trip(trip_dir):
    trip_dir = Path(trip_dir)
    tid = trip_dir.name
    base = trip_dir / tid
    track = _read(f"{base}.track", ["lon", "lat", "t"])
    nodes = _read(f"{base}.nodes", ["lon", "lat"])
    arcs = _read(f"{base}.arcs", ["from_node", "to_node"], dtype=int)
    route_file = Path(f"{base}.route")
    route = None
    if route_file.exists():
        route = _read(route_file, ["arc_id"], dtype=int)["arc_id"].to_numpy()
    return {"id": tid, "track": track, "nodes": nodes, "arcs": arcs, "route": route}
