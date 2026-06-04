import os
import random
import time

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)
FAILURE_RATE      = float(os.environ.get("FAILURE_RATE", 0.0))   # 0.0–1.0
EXTRA_LATENCY_MS  = int(os.environ.get("EXTRA_LATENCY_MS", 0))   # milisegundos

ZONES = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

print("Cargando dataset...")
df_full = pd.read_csv(
    "/data/buildings.csv",
    usecols=["latitude", "longitude", "area_in_meters", "confidence"],
)
data = {}
for zone_id, bbox in ZONES.items():
    mask = (
        (df_full["latitude"] >= bbox["lat_min"]) & (df_full["latitude"] <= bbox["lat_max"]) &
        (df_full["longitude"] >= bbox["lon_min"]) & (df_full["longitude"] <= bbox["lon_max"])
    )
    data[zone_id] = df_full[mask].reset_index(drop=True)
    print(f"  {zone_id}: {len(data[zone_id])} edificios")

def zone_area_km2(zone_id):
    b = ZONES[zone_id]
    lat_diff = abs(b["lat_max"] - b["lat_min"]) * 111
    lon_diff = abs(b["lon_max"] - b["lon_min"]) * 111 * np.cos(
        np.radians((b["lat_min"] + b["lat_max"]) / 2)
    )
    return lat_diff * lon_diff

@app.route("/query", methods=["POST"])
def query():
    if FAILURE_RATE > 0 and random.random() < FAILURE_RATE:
        return jsonify({"error": "simulated failure"}), 503
    if EXTRA_LATENCY_MS > 0:
        time.sleep(EXTRA_LATENCY_MS / 1000.0)
    body = request.json
    q     = body["query_type"]
    zone  = body["zone_id"]
    conf  = body.get("confidence_min", 0.0)
    bins  = body.get("bins", 5)
    zone2 = body.get("zone_id_b", None)

    df       = data[zone]
    filtered = df[df["confidence"] >= conf]

    if q == "Q1":
        result = {"count": int(len(filtered))}

    elif q == "Q2":
        areas  = filtered["area_in_meters"]
        result = {
            "avg_area":   float(areas.mean()),
            "total_area": float(areas.sum()),
            "n":          int(len(areas)),
        }

    elif q == "Q3":
        result = {"density": float(len(filtered) / zone_area_km2(zone))}

    elif q == "Q4":
        df2       = data[zone2]
        filtered2 = df2[df2["confidence"] >= conf]
        da = len(filtered)  / zone_area_km2(zone)
        db = len(filtered2) / zone_area_km2(zone2)
        result = {
            "zone_a": float(da),
            "zone_b": float(db),
            "winner": zone if da > db else zone2,
        }

    elif q == "Q5":
        scores = df["confidence"].values
        counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
        result = {
            "distribution": [
                {"bucket": i, "min": float(edges[i]), "max": float(edges[i + 1]), "count": int(counts[i])}
                for i in range(bins)
            ]
        }

    else:
        result = {"error": "unknown query type"}

    return jsonify(result)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "failure_rate": FAILURE_RATE})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)