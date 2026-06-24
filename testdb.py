from db import DatabaseManager
from datetime import datetime, timedelta
import random


def test_db():
    """Prueba completa de la base de datos"""

    db = DatabaseManager("test_detecciones.db")

    print("\n1. Guardando detecciones de prueba")
    objetos = ["person", "car", "dog", "cat", "bicycle", "motorbike"]

    for i in range(20):
        objeto = random.choice(objetos)
        conf = round(random.uniform(0.75, 0.98), 2)
        timestamp = (datetime.now() - timedelta(minutes=i)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if db.guardar_deteccion(objeto, conf, timestamp):
            print(f"  Guardado: {objeto} ({conf})")

    print("\n2. Estadísticas:")
    stats = db.obtener_estadisticas()
    print(f"  Total: {stats['total']}")
    print(f"  Promedio confianza: {stats['promedio_confianza']:.2f}")
    print("  Por objeto:")
    for obj, cant in stats["por_objeto"]:
        print(f"  {obj}: {cant}")

    print("\n3. Últimas 5 detecciones:")
    ultimas = db.obtener_ultimas(5)
    for reg in ultimas:
        print(f"  • {reg[1]} ({reg[2]:.2f}) - {reg[3]}")

    print("\n4. Búsqueda de 'person':")
    resultados = db.buscar("person")
    print(f"  Encontrados: {len(resultados)} registros")

    print("\n5. Exportando a CSV...")
    db.exportar_csv("test_export.csv", limite=10)

    print("\n6. Limpiando registros antiguos (1 día)...")
    eliminados = db.limpiar_antiguos(1)

    print("\n7. Información de la BD:")
    info = db.obtener_info_db()
    print(f"  Ruta: {info['ruta']}")
    print(f"  Tamaño: {info['tamaño_mb']} MB")
    print(f"  Última fecha: {info['ultima_fecha']}")


if __name__ == "__main__":
    test_db()
