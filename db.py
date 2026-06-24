import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any


class DatabaseManager:
    """
    Gestor de base de datos SQLite para detecciones de YOLO
    """

    def __init__(self, db_path: str = "detecciones.db"):
        """
        Inicializar gestor de base de datos

        Args:
            db_path: Ruta del archivo de base de datos
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Crear tabla si no existe y verificar integridad"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Crear tabla principal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detecciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objeto TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    origen TEXT DEFAULT 'camera',
                    procesado BOOLEAN DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_objeto 
                ON detecciones(objeto)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fecha_hora 
                ON detecciones(fecha_hora)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON detecciones(timestamp)
            """)

            conn.commit()
            conn.close()
            print(f"Base de datos inicializada: {self.db_path}")

        except Exception as e:
            print(f"Error al inicializar BD: {e}")
            raise

    def guardar_deteccion(
        self, objeto: str, confidence: float, timestamp: str, origen: str = "camera"
    ) -> bool:
        """
        Guardar una detección en la base de datos

        Args:
            objeto: Nombre del objeto detectado
            confidence: Nivel de confianza (0-1)
            timestamp: Timestamp en formato string
            origen: Origen de la detección (camera/video/archivo)

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO detecciones (objeto, confidence, timestamp, origen)
                VALUES (?, ?, ?, ?)
            """,
                (objeto, confidence, timestamp, origen),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error al guardar en BD: {e}")
            return False

    def guardar_multiples(self, detecciones: List[Dict[str, Any]]) -> int:
        """
        Guardar múltiples detecciones en lote

        Args:
            detecciones: Lista de diccionarios con datos

        Returns:
            int: Número de registros guardados
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            datos = []
            for det in detecciones:
                datos.append(
                    (
                        det.get("objeto", "unknown"),
                        det.get("confidence", 0.0),
                        det.get(
                            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ),
                        det.get("origen", "camera"),
                    )
                )

            cursor.executemany(
                """
                INSERT INTO detecciones (objeto, confidence, timestamp, origen)
                VALUES (?, ?, ?, ?)
            """,
                datos,
            )

            conn.commit()
            guardados = cursor.rowcount
            conn.close()
            return guardados

        except Exception as e:
            print(f"Error al guardar múltiples registros: {e}")
            return 0

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales

        Returns:
            Dict con estadísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total de detecciones
            cursor.execute("SELECT COUNT(*) FROM detecciones")
            total = cursor.fetchone()[0]

            # Detecciones por objeto
            cursor.execute("""
                SELECT objeto, COUNT(*) as cantidad 
                FROM detecciones 
                GROUP BY objeto 
                ORDER BY cantidad DESC
            """)
            por_objeto = cursor.fetchall()

            # Promedio de confianza
            cursor.execute("""
                SELECT AVG(confidence), MIN(confidence), MAX(confidence)
                FROM detecciones
            """)
            avg_conf, min_conf, max_conf = cursor.fetchone()

            # Últimas 5 detecciones
            cursor.execute("""
                SELECT objeto, confidence, timestamp, fecha_hora
                FROM detecciones 
                ORDER BY id DESC 
                LIMIT 5
            """)
            ultimas = cursor.fetchall()

            # Detecciones por día (últimos 7 días)
            cursor.execute("""
                SELECT DATE(fecha_hora) as dia, COUNT(*) as total
                FROM detecciones
                WHERE fecha_hora >= datetime('now', '-7 days')
                GROUP BY dia
                ORDER BY dia DESC
            """)
            por_dia = cursor.fetchall()

            conn.close()

            return {
                "total": total,
                "por_objeto": por_objeto,
                "ultimas": ultimas,
                "promedio_confianza": avg_conf or 0,
                "min_confianza": min_conf or 0,
                "max_confianza": max_conf or 0,
                "por_dia": por_dia,
            }

        except Exception as e:
            print(f"Error al obtener estadísticas: {e}")
            return {}

    def obtener_por_fecha(self, fecha_inicio: str, fecha_fin: str) -> List[Tuple]:
        """
        Obtener detecciones en un rango de fechas

        Args:
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)

        Returns:
            Lista de registros
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, objeto, confidence, timestamp, fecha_hora, origen
                FROM detecciones
                WHERE DATE(fecha_hora) BETWEEN ? AND ?
                ORDER BY fecha_hora DESC
            """,
                (fecha_inicio, fecha_fin),
            )

            resultados = cursor.fetchall()
            conn.close()
            return resultados

        except Exception as e:
            print(f"Error al consultar por fecha: {e}")
            return []

    def obtener_por_objeto(self, objeto: str, limite: int = 50) -> List[Tuple]:
        """
        Obtener detecciones de un objeto específico

        Args:
            objeto: Nombre del objeto
            limite: Número máximo de registros

        Returns:
            Lista de registros
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, objeto, confidence, timestamp, fecha_hora
                FROM detecciones
                WHERE objeto = ?
                ORDER BY fecha_hora DESC
                LIMIT ?
            """,
                (objeto, limite),
            )

            resultados = cursor.fetchall()
            conn.close()
            return resultados

        except Exception as e:
            print(f" Error al consultar por objeto: {e}")
            return []

    def obtener_ultimas(self, n: int = 10) -> List[Tuple]:
        """
        Obtener las últimas N detecciones

        Args:
            n: Número de registros a obtener

        Returns:
            Lista de registros
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, objeto, confidence, timestamp, fecha_hora
                FROM detecciones
                ORDER BY id DESC
                LIMIT ?
            """,
                (n,),
            )

            resultados = cursor.fetchall()
            conn.close()
            return resultados

        except Exception as e:
            print(f"Error al obtener últimas detecciones: {e}")
            return []

    def buscar(self, termino: str) -> List[Tuple]:
        """
        Buscar detecciones por objeto o timestamp

        Args:
            termino: Texto a buscar

        Returns:
            Lista de registros
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, objeto, confidence, timestamp, fecha_hora
                FROM detecciones
                WHERE objeto LIKE ? OR timestamp LIKE ?
                ORDER BY fecha_hora DESC
                LIMIT 100
            """,
                (f"%{termino}%", f"%{termino}%"),
            )

            resultados = cursor.fetchall()
            conn.close()
            return resultados

        except Exception as e:
            print(f"Error al buscar: {e}")
            return []

    def limpiar_antiguos(self, dias: int = 30) -> int:
        """
        Eliminar detecciones más antiguas que X días

        Args:
            dias: Número de días a conservar

        Returns:
            int: Número de registros eliminados
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM detecciones 
                WHERE fecha_hora < datetime('now', ?)
            """,
                (f"-{dias} days",),
            )

            eliminados = cursor.rowcount
            conn.commit()
            conn.close()

            print(f"Eliminados {eliminados} registros antiguos (> {dias} días)")
            return eliminados

        except Exception as e:
            print(f"Error al limpiar registros: {e}")
            return 0

    def exportar_csv(
        self, archivo: str = "exportacion.csv", limite: int = 1000
    ) -> bool:
        """
        Exportar detecciones a archivo CSV

        Args:
            archivo: Nombre del archivo CSV
            limite: Límite de registros a exportar

        Returns:
            bool: True si se exportó correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, objeto, confidence, timestamp, fecha_hora, origen
                FROM detecciones
                ORDER BY id DESC
                LIMIT ?
            """,
                (limite,),
            )

            import csv

            with open(archivo, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["ID", "Objeto", "Confidence", "Timestamp", "Fecha_Hora", "Origen"]
                )
                writer.writerows(cursor.fetchall())

            conn.close()
            print(f"Exportados datos a {archivo}")
            return True

        except Exception as e:
            print(f"Error al exportar CSV: {e}")
            return False

    def vaciar_tabla(self, confirmar: bool = False) -> bool:
        """
        Vaciar todos los registros de la tabla

        Args:
            confirmar: Debe ser True para ejecutar

        Returns:
            bool: True si se vació correctamente
        """
        if not confirmar:
            print("Para vaciar la tabla, confirma con confirmar=True")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM detecciones")
            conn.commit()
            conn.close()

            print("Tabla vaciada completamente")
            return True

        except Exception as e:
            print(f"Error al vaciar tabla: {e}")
            return False

    # utils

    def obtener_conexion(self):
        """Obtener conexión directa para consultas personalizadas"""
        return sqlite3.connect(self.db_path)

    def ejecutar_consulta(self, query: str, params: tuple = ()) -> List[Tuple]:
        """
        Ejecutar consulta SQL personalizada

        Args:
            query: Consulta SQL
            params: Parámetros para la consulta

        Returns:
            Lista de resultados
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            return resultados

        except Exception as e:
            print(f"Error en consulta personalizada: {e}")
            return []

    def obtener_info_db(self) -> Dict[str, Any]:
        """
        Obtener información de la base de datos

        Returns:
            Dict con información
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Tamaño del archivo
            import os

            tamaño = (
                os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            )

            # Número de tablas
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table'
            """)
            num_tablas = cursor.fetchone()[0]

            # Última fecha
            cursor.execute("""
                SELECT MAX(fecha_hora) FROM detecciones
            """)
            ultima_fecha = cursor.fetchone()[0]

            conn.close()

            return {
                "ruta": self.db_path,
                "tamaño_bytes": tamaño,
                "tamaño_mb": round(tamaño / (1024 * 1024), 2),
                "num_tablas": num_tablas,
                "ultima_fecha": ultima_fecha,
            }

        except Exception as e:
            print(f"Error al obtener info BD: {e}")
            return {}

