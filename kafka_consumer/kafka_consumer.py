import json
import os
import time

import requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BOOTSTRAP  = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
CONSUMER_GROUP   = os.environ.get("CONSUMER_GROUP", "query-processors")
TOPIC_MAIN       = os.environ.get("TOPIC_MAIN", "queries")
TOPIC_RETRY      = os.environ.get("TOPIC_RETRY", "queries-retry")
TOPIC_DLQ        = os.environ.get("TOPIC_DLQ", "queries-dlq")
MAX_RETRIES      = int(os.environ.get("MAX_RETRIES", 3))

CACHE_URL    = "http://cache_service:8001/query"
METRICS_URL  = "http://metrics:8003/record"

def wait_for_kafka():
    for attempt in range(30):
        try:
            p = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
            p.close()
            print("[Consumer] Kafka disponible.")
            return
        except NoBrokersAvailable:
            print(f"[Consumer] Esperando Kafka... {attempt+1}/30")
            time.sleep(5)
    raise RuntimeError("Kafka no disponible tras 30 intentos")
def make_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
    )
def make_consumer(topics):
    return KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        max_poll_interval_ms=300000,
    )
def record(event: dict):
    try:
        requests.post(METRICS_URL, json=event, timeout=2)
    except Exception:
        pass  # métricas no bloquean el flujo principal
def process(msg: dict, producer: KafkaProducer):
    query_id    = msg.get("id", "unknown")
    retry_count = msg.get("retry_count", 0)
    created_at  = msg.get("created_at", time.time())

    start = time.time()
    try:
        resp = requests.post(CACHE_URL, json=msg, timeout=10)
        resp.raise_for_status()
        data    = resp.json()
        latency = time.time() - start
        source  = data.get("source", "unknown")

        record({
            "type":         "processed",
            "source":       source,           # "cache" | "generator"
            "query":        msg.get("query_type"),
            "zone":         msg.get("zone_id"),
            "latency":      latency,
            "retry_count":  retry_count,
            "total_time":   time.time() - created_at,
            "recovered":    retry_count > 0,  # True si venía de reintentos
            "id":           query_id,
        })
        status = "HIT" if source == "cache" else "MISS"
        print(f"[Consumer] OK {status} | {msg.get('query_type')} {msg.get('zone_id')} "
              f"| retry={retry_count} | lat={latency:.3f}s | id={query_id[:8]}")

    except Exception as e:
        latency = time.time() - start
        print(f"[Consumer] FALLO | {msg.get('query_type')} {msg.get('zone_id')} "
              f"| retry={retry_count} | err={e} | id={query_id[:8]}")

        if retry_count < MAX_RETRIES:
            msg["retry_count"] = retry_count + 1
            producer.send(TOPIC_RETRY, value=msg)
            record({
                "type":        "retry",
                "query":       msg.get("query_type"),
                "zone":        msg.get("zone_id"),
                "retry_count": msg["retry_count"],
                "latency":     latency,
                "id":          query_id,
                "error":       str(e),
            })
            print(f"[Consumer] → RETRY {msg['retry_count']}/{MAX_RETRIES} | id={query_id[:8]}")
        else:
            msg["failed_reason"] = str(e)
            msg["failed_at"]     = time.time()
            producer.send(TOPIC_DLQ, value=msg)
            record({
                "type":        "dlq",
                "query":       msg.get("query_type"),
                "zone":        msg.get("zone_id"),
                "retry_count": retry_count,
                "latency":     latency,
                "id":          query_id,
                "error":       str(e),
            })
            print(f"[Consumer] → DLQ | id={query_id[:8]}")

def main():
    wait_for_kafka()
    producer = make_producer()
    # Consume tanto el tópico principal como el de reintentos
    consumer = make_consumer([TOPIC_MAIN, TOPIC_RETRY])

    print(f"[Consumer] Escuchando tópicos: {TOPIC_MAIN}, {TOPIC_RETRY} | grupo={CONSUMER_GROUP}")

    for kafka_msg in consumer:
        topic = kafka_msg.topic
        msg   = kafka_msg.value
        print(f"[Consumer] Recibido desde '{topic}' | id={msg.get('id','?')[:8]} "
              f"| retry={msg.get('retry_count',0)}")
        process(msg, producer)

if __name__ == "__main__":
    main()