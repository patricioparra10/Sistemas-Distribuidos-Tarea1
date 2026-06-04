echo "==============="
echo "Reintentos"
echo "==============="

echo " Reiniciando con FAILURE_RATE=0.3."
docker-compose down
sleep 3

cat > /tmp/docker-compose.override.yml << 'OVERRIDE'
version: '3.8'
services:
  response_generator:
    environment:
      - FAILURE_RATE=0.3
      - EXTRA_LATENCY_MS=0
OVERRIDE

docker-compose -f docker-compose.yml -f /tmp/docker-compose.override.yml up -d --scale kafka_consumer=1
sleep 25

echo "Reseteando métricas."
curl -s -X POST http://localhost:8003/reset > /dev/null
echo "OK"

echo " Enviando consultas"
docker-compose -f docker-compose.yml -f /tmp/docker-compose.override.yml run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=500 \
  -e REQUESTS_PER_SECOND=10 \
  traffic_generator

echo "Esperando reintentos y recuperación"
sleep 40

echo "Resultados guardados"
RESULT=$(curl -s http://localhost:8003/summary)
echo $RESULT | python3 -m json.tool > escenarios/resultado_escenario5.json
echo "Resultado guardado en escenarios/resultado_escenario5.json"

echo ""
echo "-- Métricas clave de reintentos --"
echo $RESULT | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Total procesadas:  {d[\"total_processed\"]}')
print(f'  Total reintentos:  {d[\"total_retries\"]}')
print(f'  Total DLQ:         {d[\"total_dlq\"]}')
print(f'  Recuperadas:       {d[\"total_recovered\"]}')
print(f'  Retry rate:        {d[\"retry_rate\"]*100:.1f}%')
print(f'  Recovery rate:     {d[\"recovery_rate\"]*100:.1f}%')
print(f'  DLQ rate:          {d[\"dlq_rate\"]*100:.1f}%')
print(f'  Latencia p50:      {d[\"latency_p50\"]*1000:.1f}ms')
print(f'  Latencia p95:      {d[\"latency_p95\"]*1000:.1f}ms')
print(f'  Recovery time p50: {d[\"recovery_time_p50\"]:.2f}s')
"

rm -f /tmp/docker-compose.override.yml