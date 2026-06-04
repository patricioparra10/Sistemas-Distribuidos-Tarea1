import json
import os
import random
import time
import uuid

import numpy as np
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# ── Configuración ──────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP    = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_MAIN         = os.environ.get("TOPIC_MAIN", "queries")
DISTRIBUTION       = os.environ.get("DISTRIBUTION", "zipf")
NUM_REQUESTS       = int(os.environ.get("NUM_REQUESTS", 500))
REQUESTS_PER_SECOND = float(os.environ.get("REQUESTS_PER_SECOND", 10))

ZONES   = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERIES = ["Q1", "Q2", "Q3", "Q4", "Q5"]

def zipf_zone():
    weights = [1 / (i + 1) for i in range(len(ZONES))]
    total   = sum(weights)
    weights = [w / total for w in weights]
    return np.random.choice(ZONES, p=weights)

def uniform_zone():
    return random.choice(ZONES)

def create_producer():
    for attempt in range(20):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",         
                retries=3,
            )
            print(f"[Producer] Conectado a Kafka en {KAFKA_BOOTSTRAP}")
            return producer
        except NoBrokersAvailable:
            print(f"[Producer] Kafka no disponible, reintento {attempt+1}/20...")
            time.sleep(5)
    raise RuntimeError("No se pudo conectar a Kafka")
def build_query():
    zone  = zipf_zone() if DISTRIBUTION == "zipf" else uniform_zone()
    q     = random.choice(QUERIES)
    conf  = random.choice([0.0, 0.5, 0.7])
    body  = {
        "id":             str(uuid.uuid4()),  #ID
        "query_type":     q,
        "zone_id":        zone,
        "confidence_min": conf,
        "bins":           5,
        "retry_count":    0,                   
        "created_at":     time.time(),         
        "distribution":   DISTRIBUTION,
    }
    if q == "Q4":
        zone2 = random.choice([z for z in ZONES if z != zone])
        body["zone_id_b"] = zone2
    return body

def main():
    delay = 1.0 / REQUESTS_PER_SECOND

    producer = create_producer()
    print(f"[Producer] Enviando {NUM_REQUESTS} consultas | dist={DISTRIBUTION} | {REQUESTS_PER_SECOND} req/s")

    sent = 0
    for i in range(NUM_REQUESTS):
        msg = build_query()
        producer.send(TOPIC_MAIN, value=msg)
        sent += 1
        print(f"[Producer] [{sent}/{NUM_REQUESTS}] {msg['query_type']} {msg['zone_id']} id={msg['id'][:8]}")
        time.sleep(delay)

    producer.flush()
    print(f"[Producer] Listo. {sent} mensajes enviados a '{TOPIC_MAIN}'.")

if __name__ == "__main__":
    main()