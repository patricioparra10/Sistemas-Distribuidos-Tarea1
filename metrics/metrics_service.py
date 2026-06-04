import time
from flask import Flask, jsonify, request

app = Flask(__name__)

events      = []       
start_time  = time.time() 
@app.route("/record", methods=["POST"])
def record():
    event = request.json
    event["timestamp"] = time.time()
    events.append(event)
    return jsonify({"ok": True})

@app.route("/summary", methods=["GET"])
def summary():
    processed = [e for e in events if e.get("type") == "processed"]
    retries   = [e for e in events if e.get("type") == "retry"]
    dlq_evts  = [e for e in events if e.get("type") == "dlq"]
    recovered = [e for e in processed if e.get("recovered")]

    total      = len(processed)
    total_sent = total + len(dlq_evts)
    elapsed    = max(time.time() - start_time, 1)
    throughput = round(total / elapsed, 4)

    latencies      = [e["latency"] for e in processed if "latency" in e]
    hit_latencies  = [e["latency"] for e in processed if e.get("source") == "cache"]
    miss_latencies = [e["latency"] for e in processed if e.get("source") == "generator"]

    def pct(data, p):
        if not data:
            return 0
        data = sorted(data)
        idx  = int(len(data) * p / 100)
        return data[min(idx, len(data) - 1)]
    retry_rate    = round(len(retries)   / total_sent, 4) if total_sent > 0 else 0
    dlq_rate      = round(len(dlq_evts)  / total_sent, 4) if total_sent > 0 else 0
    recovery_rate = round(len(recovered) / max(len(retries), 1), 4)

    recovery_times = [e.get("total_time", 0) for e in recovered if "total_time" in e]
    hits   = sum(1 for e in processed if e.get("source") == "cache")
    misses = sum(1 for e in processed if e.get("source") == "generator")

    return jsonify({
        # volumen
        "total_processed":  total,
        "total_retries":    len(retries),
        "total_dlq":        len(dlq_evts),
        "total_recovered":  len(recovered),
        # caché
        "hits":             hits,
        "misses":           misses,
        "hit_rate":         round(hits / total, 4) if total > 0 else 0,
        # throughput
        "throughput_rps":   throughput,
        "elapsed_seconds":  round(elapsed, 2),
        # latencia general
        "latency_p50":      pct(latencies, 50),
        "latency_p95":      pct(latencies, 95),
        # latencia por tipo
        "hit_latency_p50":  pct(hit_latencies, 50),
        "hit_latency_p95":  pct(hit_latencies, 95),
        "miss_latency_p50": pct(miss_latencies, 50),
        "miss_latency_p95": pct(miss_latencies, 95),
        # tasas
        "retry_rate":       retry_rate,
        "dlq_rate":         dlq_rate,
        "recovery_rate":    recovery_rate,
        # recovery time
        "recovery_time_p50": pct(recovery_times, 50),
        "recovery_time_p95": pct(recovery_times, 95),
    })
@app.route("/events", methods=["GET"])
def get_events():
    return jsonify(events)

@app.route("/reset", methods=["POST"])
def reset():
    global events, start_time
    events     = []
    start_time = time.time()
    return jsonify({"ok": True, "reset_at": start_time})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)