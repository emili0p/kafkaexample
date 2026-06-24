import cv2
import json
import time

from kafka import KafkaProducer
from ultralytics import YOLO
from db import DatabaseManager

model = YOLO("yolov8n.pt")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

db = DatabaseManager("detecciones.db")

ultimo_envio = 0
contador_detecciones = 0


def conectar_camara():
    while True:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("Camara conectada")
            return cap
        print("No se pudo conectar la cámara. Reintentando...")
        time.sleep(2)


def mostrar_estadisticas():
    """Mostrar estadísticas en consola"""
    stats = db.obtener_estadisticas()

    if not stats:
        print("No se pudieron obtener estadísticas")
        return

    print("\n" + "=" * 60)
    print("eSTADÍSTICAS DE DETECCIONES")
    print("=" * 60)
    print(f"Total detecciones: {stats['total']}")
    print(f"Confianza promedio: {stats['promedio_confianza']:.2f}")
    print(f"Confianza mínima: {stats['min_confianza']:.2f}")
    print(f"Confianza máxima: {stats['max_confianza']:.2f}")

    print("\n Por objeto:")
    for objeto, cantidad in stats["por_objeto"]:
        print(f"  • {objeto}: {cantidad}")

    print("\nÚltimos 7 días:")
    for dia, total in stats["por_dia"]:
        print(f"  • {dia}: {total} detecciones")

    print("\nÚltimas 5 detecciones:")
    for objeto, conf, ts, fh in stats["ultimas"]:
        print(f"  • {objeto} ({conf:.2f}) - {ts}")

    print("=" * 60 + "\n")


cap = conectar_camara()

print("\nSISTEMA DE DETECCIÓN INICIADO")
print("-" * 40)
print(" Comandos:")
print("  • 'q' - Salir")
print("  • 's' - Ver estadísticas")
print("  • 'l' - Limpiar registros antiguos (30 días)")
print("  • 'e' - Exportar a CSV")
print("  • 'v' - Vaciar tabla (requiere confirmación)")
print("-" * 40 + "\n")

while True:
    try:
        ret, frame = cap.read()

        if not ret:
            print("Cámara desconectada")
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

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                # Guardar en base de datos
                if db.guardar_deteccion(objeto, conf, timestamp):
                    contador_detecciones += 1
                    print(f"BD: {objeto} (conf: {conf:.2f}) - #{contador_detecciones}")

                if time.time() - ultimo_envio >= 2:
                    data = {
                        "objeto": objeto,
                        "confidence": round(conf, 2),
                        "timestamp": timestamp,
                    }

                    try:
                        producer.send("detecciones", data)
                        ultimo_envio = time.time()
                        print(f"Kafka: {data}")
                    except Exception as e:
                        print(f"Error Kafka: {e}")

        # Mostrar frame
        cv2.imshow("Detecciones - YOLO + SQLite + Kafka", annotated_frame)

        # Controles de teclado
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("s"):
            mostrar_estadisticas()
        elif key == ord("l"):
            eliminados = db.limpiar_antiguos(30)
            print(f"Limpieza completada. Eliminados {eliminados} registros")
        elif key == ord("e"):
            db.exportar_csv()
        elif key == ord("v"):
            confirm = input("¿Seguro que quieres vaciar la tabla? (s/N): ")
            if confirm.lower() == "s":
                db.vaciar_tabla(confirmar=True)

    except KeyboardInterrupt:
        print("\nInterrupción por usuario")
        break
    except Exception as e:
        print(f"❌ ERROR: {e}")
        time.sleep(2)

cap.release()
cv2.destroyAllWindows()

print("\n" + "=" * 60)
print("PROGRAMA FINALIZADO")
print(f"Total detecciones registradas: {contador_detecciones}")
print("=" * 60)

mostrar_estadisticas()

producer.flush()
producer.close()
