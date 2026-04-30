import requests, random, numpy as np, os, time, json

CACHE_URL = "http://cache_service:8001/query"
ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERIES = ["Q1", "Q2", "Q3", "Q4", "Q5"]
DIST = os.environ.get("DISTRIBUTION", "zipf")
NUM_REQUESTS = int(os.environ.get("NUM_REQUESTS", 500))

def zipf_zone():
    # Zipf: Z1 es la más popular
    weights = [1/(i+1) for i in range(len(ZONES))]
    total = sum(weights)
    weights = [w/total for w in weights]
    return np.random.choice(ZONES, p=weights)

def uniform_zone():
    return random.choice(ZONES)

time.sleep(10)  # esperar que los servicios levanten

results = []
for i in range(NUM_REQUESTS):
    zone = zipf_zone() if DIST == "zipf" else uniform_zone()
    q = random.choice(QUERIES)
    conf = random.choice([0.0, 0.5, 0.7])
    body = {"query_type": q, "zone_id": zone, "confidence_min": conf, "bins": 5}
    if q == "Q4":
        zone2 = random.choice([z for z in ZONES if z != zone])
        body["zone_id_b"] = zone2

    try:
        resp = requests.post(CACHE_URL, json=body, timeout=10)
        results.append({"request": i, "zone": zone, "query": q, "source": resp.json().get("source")})
        print(f"[{i+1}/{NUM_REQUESTS}] {q} {zone} -> {resp.json().get('source')}")
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(0.05)  # ~20 req/seg

with open("/tmp/traffic_results.json", "w") as f:
    json.dump(results, f)

print("DONE. Resultados guardados.")