echo "=================="
echo "Falla Temporal"
echo "=================="

docker-compose up -d --scale kafka_consumer=1
sleep 20

echo "Reseteando métricas."
curl -s -X POST http://localhost:8003/reset > /dev/null
echo "OK"

echo "Fase NORMAL enviando consultas"
docker-compose run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=300 \
  -e REQUESTS_PER_SECOND=10 \
  traffic_generator &
PRODUCER_PID=$!

sleep 10

echo " deteniendo response_generator."
docker-compose stop response_generator
echo "  response_generator detenidp. Las consultas quedarán en backlog de Kafka."

echo "  Midiendo backlog durante falla..."
for i in 1 2 3 4 5; do
  sleep 5
  BACKLOG=$(docker-compose exec kafka kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --group query-processors \
    --describe 2>/dev/null | awk 'NR>1 {sum+=$6} END {print sum}')
  echo "  [t+${i}0s] Backlog estimado: ${BACKLOG:-'calculando...'} mensajes pendientes"
done

echo "Fase RECUPERACIÓN - reiniciando response_generator..."
docker-compose start response_generator
sleep 10
echo "  response_generator RESTAURADO."

echo "Esperando vaciado de cola (30s)..."
sleep 30

wait $PRODUCER_PID 2>/dev/null

echo "Guardando métricas del escenario 4."
curl -s http://localhost:8003/summary | python3 -m json.tool > escenarios/resultado_escenario4.json
echo "Resultados guardados"
cat escenarios/resultado_escenario4.json