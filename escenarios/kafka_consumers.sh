#!/bin/bash

echo "==============================="
echo " Kafka + Múltiples Consumers"
echo "==============================="

N_CONSUMERS=3
ARCHIVO="escenarios/resultado_escenario3.json"

echo ""
echo "--- Probando con $N_CONSUMERS consumer(s) ---"

echo "  Deteniendo sistema."
docker-compose down
sleep 3

echo "  Levantando con $N_CONSUMERS consumer(s)..."
docker-compose up -d --scale kafka_consumer=$N_CONSUMERS
sleep 30

curl -s -X POST http://localhost:8003/reset > /dev/null

echo "  Enviando consultas."
docker-compose run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=500 \
  -e REQUESTS_PER_SECOND=20 \
  traffic_generator
sleep 20

curl -s http://localhost:8003/summary | python3 -m json.tool > $ARCHIVO
echo "  Resultado guardado en $ARCHIVO"

THROUGHPUT=$(cat $ARCHIVO | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['throughput_rps'])")
LAT_P50=$(cat $ARCHIVO | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['latency_p50'])")
LAT_P95=$(cat $ARCHIVO | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['latency_p95'])")

echo ""
echo "---- RESUMEN ESCENARIO 3 ----"
echo "  $N_CONSUMERS consumers: throughput=$THROUGHPUT rps, p50=$LAT_P50 s, p95=$LAT_P95 s"