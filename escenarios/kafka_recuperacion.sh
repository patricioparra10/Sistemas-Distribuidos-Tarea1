#!/bin/bash

echo "=========================================================="
echo " Escenario 7: Recuperación ante Fallos (Síncrono vs Kafka)"
echo "=========================================================="

ARCHIVO_UNICO="escenarios/resultado_escenario7.json"

echo ""
echo "---Evaluación de la Arquitectura Síncrona ---"
docker-compose up -d --scale kafka_consumer=1
sleep 20

echo "[A2] Reseteando métricas del servicio..."
curl -s -X POST http://localhost:8003/reset > /dev/null

echo "Deteniendo response_generator simulando caída crítica."
docker-compose stop response_generator
sleep 2

echo "Enviando consultas síncronas."
SYNC_SENT=0
SYNC_FAILED=0

for i in $(seq 1 100); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8001/query \
    -H "Content-Type: application/json" \
    -d '{"query_type":"Q1","zone_id":"Z1","confidence_min":0.0,"bins":5}' \
    --max-time 2)

  if [ "$STATUS" = "200" ]; then
    SYNC_SENT=$((SYNC_SENT + 1))
  else
    SYNC_FAILED=$((SYNC_FAILED + 1))
  fi
done

TOTAL_SYNC=$((SYNC_SENT + SYNC_FAILED))
TASA_PERDIDA_SYNC=$(python3 -c "print(round(($SYNC_FAILED / $TOTAL_SYNC) * 100, 2))")
echo "  → Síncrono Completado - Enviadas: $TOTAL_SYNC | Exitosas: $SYNC_SENT | PERDIDAS: $SYNC_FAILED ($TASA_PERDIDA_SYNC%)"

echo "[A5] Restaurando response_generator..."
docker-compose start response_generator
sleep 10

echo ""
echo "--- Evaluación de la Arquitectura con Kafka ---"
echo "Reseteando métricas."
curl -s -X POST http://localhost:8003/reset > /dev/null

echo " Iniciando envío en paralelo de 200 consultas"
docker-compose run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=200 \
  -e REQUESTS_PER_SECOND=20 \
  traffic_generator &
PRODUCER_PID=$!

sleep 5
echo "Simulando falla temporal: Deteniendo response_generator (10s)"
docker-compose stop response_generator
sleep 10

echo " Recuperación: Reiniciando response_generator."
docker-compose start response_generator
sleep 5

wait $PRODUCER_PID 2>/dev/null
echo "  → Tráfico enviado por completo. Esperando drenado de mensajes (20s)..."
sleep 20

echo ""
echo "--- Generando Reporte Comparativo Único ---"

KAFKA_RESULT=$(curl -s http://localhost:8003/summary)

KAFKA_PROCESSED=$(echo $KAFKA_RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_processed', 0))")
KAFKA_DLQ=$(echo $KAFKA_RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_dlq', 0))")
KAFKA_RECOVERED=$(echo $KAFKA_RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_recovered', 0))")

python3 - > $ARCHIVO_UNICO << PYEOF
import json

data = {
    "escenario": "Recuperación ante Fallos (Comparativa Tarea 1 vs Tarea 2)",
    "arquitectura_sincrona_t1": {
        "consultas_enviadas": $TOTAL_SYNC,
        "consultas_exitosas": $SYNC_SENT,
        "consultas_perdidas": $SYNC_FAILED,
        "tasa_perdida_porcentaje": $TASA_PERDIDA_SYNC
    },
    "arquitectura_kafka_t2": {
        "consultas_procesadas": $KAFKA_PROCESSED,
        "consultas_recuperadas_tras_falla": $KAFKA_RECOVERED,
        "consultas_enviadas_dlq": $KAFKA_DLQ
    }
}

print(json.dumps(data, indent=4))
PYEOF

echo ""
echo "========== RESUMEN GENERADO EN JSON =========="
echo "  SÍNCRONO T1  -> Perdidas: $SYNC_FAILED de $TOTAL_SYNC ($TASA_PERDIDA_SYNC%)"
echo "  KAFKA T2     -> Procesadas en total: $KAFKA_PROCESSED | Recuperadas del Backlog: $KAFKA_RECOVERED | Enviadas a DLQ: $KAFKA_DLQ"