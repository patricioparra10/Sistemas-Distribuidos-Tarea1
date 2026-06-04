set -e
cd "$(dirname "$0")/.."

echo ""
echo "############################"
echo "  Todos los Escenarios"
echo "############################"
echo ""

chmod +x escenarios/*.sh

run_scenario() {
  local num=$1
  local name=$2
  local script=$3
  echo ""
  echo "====================================="
  echo "  Iniciando Escenario $num: $name"
  echo "====================================="
  bash $script
  echo ""
  echo "  Escenario $num completado."
  sleep 5
}

run_scenario 2 "Kafka + 1 Consumer"          "escenarios/kafka_1consumer.sh"
run_scenario 3 "Kafka + Múltiples Consumers"  "escenarios/kafka_consumers.sh"
run_scenario 4 "Falla Temporal"               "escenarios/kafka_faail.sh"
run_scenario 5 "Reintentos"                   "escenarios/kafka_reintento.sh"
run_scenario 6 "Spike de Tráfico"             "escenarios/kafka_spike.sh"
run_scenario 7 "Recuperación ante Fallos"     "escenarios/kafka_recuperacion.sh"

echo ""
echo "  Todos los escenarios completados."
