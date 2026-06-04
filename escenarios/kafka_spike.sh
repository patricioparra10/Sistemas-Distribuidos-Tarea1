#!/bin/bash

echo "==================================="
echo " Escenario 6: Spike de Tráfico"
echo "==================================="

ARCHIVO="escenarios/resultado_escenario6.json"

docker-compose down
sleep 3
docker-compose up -d --scale kafka_consumer=1
sleep 25

curl -s -X POST http://localhost:8003/reset > /dev/null

echo "Generando spike de trafico."
docker-compose run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=300 \
  -e REQUESTS_PER_SECOND=100 \
  traffic_generator

echo "  Esperando a que el consumer procese el backlog acumulado"
sleep 30

echo "Extrayendo métricas generales del spike."
curl -s http://localhost:8003/summary | python3 -m json.tool > $ARCHIVO
echo "  Resultado único guardado exitosamente en: $ARCHIVO"

echo ""
echo "=== RESUMEN ESCENARIO 6 ==="
python3 - << 'PYEOF'
import json
with open("escenarios/resultado_escenario6.json") as f: data = json.load(f)

print(f"  Consultas Procesadas : {data['total_processed']}")
print(f"  Throughput del Hito  : {data['throughput_rps']:.2f} rps")
print(f"  Latencia p50 (Mediana): {data['latency_p50']*1000:.1f} ms")
print(f"  Latencia p95 (Máxima) : {data['latency_p95']*1000:.1f} ms")
PYEOF