"""Step 1: draw one trip on an interactive Folium map.

Usage (repo root):
  python -m maps.plot_trip train 00000005
  python -m maps.plot_trip student_test 00000007
Output: results/map_<trip>.html  (open in a browser)
"""
import sys
from pathlib import Path

import folium

from data_processing.loader import DATA_ROOT, load_trip


def build_map(d, pad=0.003):
    tr, nodes, arcs, route = d["track"], d["nodes"], d["arcs"], d["route"]
    centre = [tr.lat.mean(), tr.lon.mean()]
    m = folium.Map(location=centre, zoom_start=14, tiles=None)

    def seg(a):  # arc id -> [[lat, lon], [lat, lon]]  (Folium wants lat, lon!)
        f, t = arcs.iloc[a]
        return [[nodes.lat[f], nodes.lon[f]], [nodes.lat[t], nodes.lon[t]]]

    # road network, only near the trajectory so the map stays light
    near = (nodes.lon.between(tr.lon.min() - pad, tr.lon.max() + pad)
            & nodes.lat.between(tr.lat.min() - pad, tr.lat.max() + pad)).to_numpy()
    net = folium.FeatureGroup("Road network (grey)", show=True)
    for a, (f, t) in enumerate(arcs.to_numpy()):
        if near[f] and near[t]:
            folium.PolyLine(seg(a), color="grey", weight=1, opacity=0.6).add_to(net)
    net.add_to(m)

    # reference route
    if route is not None:
        ref = folium.FeatureGroup("Reference route (green)", show=True)
        for a in route:
            folium.PolyLine(seg(a), color="green", weight=9, opacity=0.55).add_to(ref)
        ref.add_to(m)

    # raw GPS points
    gps = folium.FeatureGroup("Raw GPS points (blue)", show=True)
    for i, r in tr.iterrows():
        folium.CircleMarker([r.lat, r.lon], radius=2, color="blue", weight=0,
                            fill=True, fill_opacity=1, tooltip=f"#{i}  t={r.t:.0f}s").add_to(gps)
    gps.add_to(m)

    m.fit_bounds([[tr.lat.min(), tr.lon.min()], [tr.lat.max(), tr.lon.max()]])
    folium.LayerControl().add_to(m)
    return m


if __name__ == "__main__":
    part, trip = sys.argv[1], sys.argv[2]
    d = load_trip(DATA_ROOT / part / trip)
    Path("results").mkdir(exist_ok=True)
    out = f"results/map_{trip}.html"
    build_map(d).save(out)
    print("saved", out)
