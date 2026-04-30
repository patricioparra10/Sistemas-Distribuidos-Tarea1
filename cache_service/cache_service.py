from flask import Flask, request, jsonify
import redis, json, time, requests

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, decode_responses=True)
TTL = 300  # segundos

METRICS_URL = "http://metrics:8003/record"
RESPONSE_URL = "http://response_generator:8002/query"

@app.route('/query', methods=['POST'])
def query():
    body = request.json
    # Construir cache key
    q = body['query_type']
    zone = body['zone_id']
    conf = body.get('confidence_min', 0.0)
    bins = body.get('bins', 5)
    zone2 = body.get('zone_id_b', '')
    cache_key = f"{q}:{zone}:{zone2}:conf={conf}:bins={bins}"

    start = time.time()
    cached = r.get(cache_key)

    if cached:
        latency = time.time() - start
        requests.post(METRICS_URL, json={"type": "hit", "query": q, "zone": zone, "latency": latency})
        return jsonify({"source": "cache", "result": json.loads(cached)})
    else:
        # Miss: pedir al generador de respuestas
        resp = requests.post(RESPONSE_URL, json=body)
        result = resp.json()
        latency = time.time() - start
        r.setex(cache_key, TTL, json.dumps(result))
        requests.post(METRICS_URL, json={"type": "miss", "query": q, "zone": zone, "latency": latency})
        return jsonify({"source": "generator", "result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)