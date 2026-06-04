# Sistema de Procesamiento Asíncrono con Apache Kafka

## Descripción General

Esta tarea implementa una arquitectura distribuida basada en Apache Kafka para el procesamiento de consultas geoespaciales sobre el dataset Google Open Buildings.

La solución extiende la arquitectura desarrollada en la Tarea 1 incorporando mensajería asíncrona, reintentos automáticos y una Dead Letter Queue (DLQ), permitiendo mejorar la tolerancia a fallos y el manejo de cargas elevadas.

El sistema utiliza Redis como caché para reducir la cantidad de consultas que requieren procesamiento completo y Kafka como mecanismo de desacoplamiento entre productores y consumidores.

---

## Tecnologías Utilizadas

* **Python 3.11**
* **Apache Kafka**
* **Apache ZooKeeper**
* **Redis 7**
* **Flask**
* **Docker**
* **Docker Compose**
* **kafka-python**
---

## Arquitectura del Sistema

El sistema está compuesto por los siguientes servicios:

# 1. Traffic Generator

Genera consultas aleatorias y las publica en Kafka mediante un Producer.

# 2. Kafka Consumer

Consume consultas desde Kafka, consulta el caché y coordina el procesamiento de las solicitudes.

# 3. Cache Service

Gestiona la comunicación con Redis y almacena respuestas previamente calculadas.

# 4. Response Generator

Procesa consultas sobre el dataset y genera respuestas cuando no existe información en caché.

# 5. Metrics Service

Registra eventos, latencias, throughput, cache hits, retries y consultas enviadas a la DLQ.

# 6. Redis

Almacena respuestas cacheadas para acelerar consultas repetidas.

# 7. Apache Kafka

Gestiona la mensajería asíncrona entre productores y consumidores.

# 8. Apache ZooKeeper

Permite la coordinación y administración de Kafka.

--

## Flujo de Procesamiento
1. El Traffic Generator genera una consulta.
2. La consulta es enviada al tópico `queries`.
3. Un consumidor Kafka recibe la consulta.
4. Se consulta el servicio de caché.
5. Si existe un cache hit, la respuesta se retorna inmediatamente.
6. Si existe un cache miss, se consulta el Response Generator.
7. Si ocurre una falla, la consulta es reenviada a `queries-retry`.
8. Si se supera el máximo de reintentos, la consulta se envía a `queries-dlq`.
9. Todos los eventos son registrados por el servicio de métricas.

---

## Instrucciones de Ejecución

Para levantar todos los servicios:

#bash
docker-compose up --build

Para detener el sistema:

#bash
docker-compose down


---

## Ejecución de Escenarios

Para ejecutar todos los escenarios de evaluación:

#bash
bash escenarios/correr_todo.sh


También es posible ejecutar cada escenario individualmente:

#bash
bash escenarios/kafka_1consumer.sh
bash escenarios/kafka_consumers.sh
bash escenarios/kafka_fail.sh
bash escenarios/kafka_reintento.sh
bash escenarios/kafka_spike.sh
bash escenarios/kafka_recuperacion.sh

---

## Configuración

La aplicación permite modificar distintos parámetros mediante variables de entorno:

* Política de caché Redis.
* Tamaño máximo de memoria.
* TTL de las entradas.
* Distribución de tráfico (Uniforme o Zipf).
* Número de consumidores Kafka.
* Tasa de fallos simulada.
* Latencia artificial.

# bash
docker-compose down
docker-compose up --build
---
