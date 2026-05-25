import cv2
import json
import time

from kafka import KafkaProducer
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("No se pudo leer la camara")
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < 0.5:
                continue

            objeto = model.names[cls]

            data = {
                "objeto": objeto,
                "confidence": round(conf, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            print(data)

            producer.send("detecciones", data)

    cv2.imshow("Kafka Vision", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
