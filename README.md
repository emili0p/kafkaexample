# Kafka example

sistema de deteccion de objetos en tiempo real usando:

- Python
- OpenCV
- YOLOv8
- Apache Kafka

## Arquitectura

Camara -> YOLO -> Kafka -> Consumer

## Arquitectura

instalar requirments con pip install -r requirements.txt


## Ejecutar

### Iniciar Kafka

./start-kafka.sh

### Crear topic

./topic.sh

### Consumer

./consumer.sh

### Producer

source venv/bin/activate
python producer.py
