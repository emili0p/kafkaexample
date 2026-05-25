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

ultimo_envio = 0


def conectar_camara():

    while True:
        cap = cv2.VideoCapture(0)

        if cap.isOpened():
            print("Camara conectada")
            return cap

        print("No se pudo conectar la camara. Reintentando...")
        time.sleep(2)


cap = conectar_camara()

while True:
    try:
        ret, frame = cap.read()

        if not ret:
            print("Camara desconectada")

            cap.release()

            time.sleep(2)

            cap = conectar_camara()

            continue

        results = model(frame)

        annotated_frame = results[0].plot()

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if conf < 0.75:
                    continue

                objeto = model.names[cls]

                # Solo personas
                if objeto != "person":
                    continue

                # Evitar spam Kafka
                if time.time() - ultimo_envio < 2:
                    continue

                data = {
                    "objeto": objeto,
                    "confidence": round(conf, 2),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                print(data)

                producer.send("detecciones", data)

                ultimo_envio = time.time()

        cv2.imshow("Kafka", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print("ERROR:", e)

        time.sleep(2)

cap.release()
cv2.destroyAllWindows()
