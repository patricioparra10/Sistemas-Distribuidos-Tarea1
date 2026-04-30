from flask import Flask, request, jsonify
import json, time

app = Flask(__name__)
events = []

@app.route('/record', methods=['POST'])
def record():
    event = request.json
    event['timestamp'] = time.time()
    events.append(event)
    return jsonify({"ok": True})

@app.route('/summary', methods=['GET'])
def summary():
    hits = sum(1 for e in events if e.get('type') == 'hit')
    misses = sum(1 for e in events if e.get('type') == 'miss')
    total = hits + misses
    hit_rate = hits / total if total > 0 else 0

    hit_latencies = [e['latency'] for e in events if e.get('type') == 'hit']
    miss_latencies = [e['latency'] for e in events if e.get('type') == 'miss']

    def percentile(data, p):
        if not data: return 0
        data = sorted(data)
        idx = int(len(data) * p / 100)
        return data[min(idx, len(data)-1)]

    return jsonify({
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hit_rate, 4),
        "total": total,
        "hit_latency_p50": percentile(hit_latencies, 50),
        "hit_latency_p95": percentile(hit_latencies, 95),
        "miss_latency_p50": percentile(miss_latencies, 50),
        "miss_latency_p95": percentile(miss_latencies, 95),
    })

@app.route('/events', methods=['GET'])
def get_events():
    return jsonify(events)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003)