echo "========================"
echo " Kafka + 1 Consumer"
echo "========================"

echo "Deteniendo sistema anterior..."
docker-compose down
sleep 3

echo " Levantando sistema con 1 consumer"
docker-compose up -d --scale kafka_consumer=1

echo "Esperando que los servicios estén listos."
sleep 30

echo " Reseteando métricas"
curl -s -X POST http://localhost:8003/reset > /dev/null
echo "OK"

echo "Enviando 500 consultas con 1 consumer."
docker-compose run --rm \
  -e DISTRIBUTION=zipf \
  -e NUM_REQUESTS=500 \
  -e REQUESTS_PER_SECOND=10 \
  traffic_generator

echo "Esperando procesamiento "
sleep 15

echo "Guardando métricas del escenario 2"
curl -s http://localhost:8003/summary | python3 -m json.tool > escenarios/resultado_escenario2.json
echo "Resultados guardados"
cat escenarios/resultado_escenario2.json