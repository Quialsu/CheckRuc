import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from config import DB_PATH

class CheckpointManager:
    """
    Manages SQLite checkpoint persistence for high-volume RUC queries (1,000 to 50,000+).
    Guarantees automatic resume without re-consulting previously processed records.
    """
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ruc_consultas (
                    ruc TEXT PRIMARY KEY,
                    razon_social TEXT,
                    fecha_inscripcion TEXT,
                    estado TEXT,
                    condicion TEXT,
                    domicilio_fiscal_original TEXT,
                    direccion TEXT,
                    distrito TEXT,
                    provincia TEXT,
                    departamento TEXT,
                    ubigeo TEXT,
                    comercio_exterior TEXT,
                    actividad_principal TEXT,
                    actividades_secundarias TEXT,
                    fuente TEXT,
                    fecha_consulta TEXT,
                    estado_consulta TEXT,
                    error_tecnico TEXT,
                    intentos INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_record(self, ruc: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ruc_consultas WHERE ruc = ?", (ruc,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_processed_rucs(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary mapping RUC -> record for all already processed RUCs
        (i.e., state in CONSULTADO or RUC NO ENCONTRADO).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ruc_consultas
                WHERE estado_consulta IN ('CONSULTADO', 'RUC NO ENCONTRADO', 'REQUIERE REVISIÓN')
            """)
            rows = cursor.fetchall()
            return {row["ruc"]: dict(row) for row in rows}

    def save_record(self, record: Dict[str, Any]):
        """
        Inserts or updates a RUC record in the SQLite database.
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ruc_consultas (
                    ruc, razon_social, fecha_inscripcion, estado, condicion,
                    domicilio_fiscal_original, direccion, distrito, provincia, departamento, ubigeo,
                    comercio_exterior, actividad_principal, actividades_secundarias,
                    fuente, fecha_consulta, estado_consulta, error_tecnico, intentos, updated_at
                ) VALUES (
                    :ruc, :razon_social, :fecha_inscripcion, :estado, :condicion,
                    :domicilio_fiscal_original, :direccion, :distrito, :provincia, :departamento, :ubigeo,
                    :comercio_exterior, :actividad_principal, :actividades_secundarias,
                    :fuente, :fecha_consulta, :estado_consulta, :error_tecnico, :intentos, :updated_at
                ) ON CONFLICT(ruc) DO UPDATE SET
                    razon_social=excluded.razon_social,
                    fecha_inscripcion=excluded.fecha_inscripcion,
                    estado=excluded.estado,
                    condicion=excluded.condicion,
                    domicilio_fiscal_original=excluded.domicilio_fiscal_original,
                    direccion=excluded.direccion,
                    distrito=excluded.distrito,
                    provincia=excluded.provincia,
                    departamento=excluded.departamento,
                    ubigeo=excluded.ubigeo,
                    comercio_exterior=excluded.comercio_exterior,
                    actividad_principal=excluded.actividad_principal,
                    actividades_secundarias=excluded.actividades_secundarias,
                    fuente=excluded.fuente,
                    fecha_consulta=excluded.fecha_consulta,
                    estado_consulta=excluded.estado_consulta,
                    error_tecnico=excluded.error_tecnico,
                    intentos=excluded.intentos,
                    updated_at=excluded.updated_at
            """, {
                "ruc": str(record.get("ruc", "")),
                "razon_social": str(record.get("razon_social", "")),
                "fecha_inscripcion": str(record.get("fecha_inscripcion", "")),
                "estado": str(record.get("estado", "")),
                "condicion": str(record.get("condicion", "")),
                "domicilio_fiscal_original": str(record.get("domicilio_fiscal_original", "")),
                "direccion": str(record.get("direccion", "")),
                "distrito": str(record.get("distrito", "")),
                "provincia": str(record.get("provincia", "")),
                "departamento": str(record.get("departamento", "")),
                "ubigeo": str(record.get("ubigeo", "")),
                "comercio_exterior": str(record.get("comercio_exterior", "")),
                "actividad_principal": str(record.get("actividad_principal", "")),
                "actividades_secundarias": str(record.get("actividades_secundarias", "")),
                "fuente": str(record.get("fuente", "")),
                "fecha_consulta": str(record.get("fecha_consulta", now)),
                "estado_consulta": str(record.get("estado_consulta", "REINTENTAR")),
                "error_tecnico": str(record.get("error_tecnico", "")),
                "intentos": int(record.get("intentos", 1)),
                "updated_at": now
            })
            conn.commit()

    def save_batch(self, records: List[Dict[str, Any]]):
        for rec in records:
            self.save_record(rec)

    def get_summary_stats(self, ruc_list: List[str]) -> Dict[str, int]:
        """
        Calculates status counts for a given target list of unique RUCs.
        """
        if not ruc_list:
            return {"total": 0, "consultados": 0, "no_encontrados": 0, "errores": 0, "pendientes": 0}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ruc_list)
            query = f"SELECT estado_consulta, COUNT(*) as count FROM ruc_consultas WHERE ruc IN ({placeholders}) GROUP BY estado_consulta"
            cursor.execute(query, ruc_list)
            rows = cursor.fetchall()

            stats_map = {row["estado_consulta"]: row["count"] for row in rows}

            consultados = stats_map.get("CONSULTADO", 0)
            no_encontrados = stats_map.get("RUC NO ENCONTRADO", 0)
            errores = stats_map.get("ERROR TEMPORAL", 0) + stats_map.get("REQUIERE REVISIÓN", 0) + stats_map.get("REINTENTAR", 0)

            total_db_records = sum(stats_map.values())
            pendientes = len(ruc_list) - (consultados + no_encontrados)
            if pendientes < 0:
                pendientes = 0

            return {
                "total": len(ruc_list),
                "consultados": consultados,
                "no_encontrados": no_encontrados,
                "errores": errores,
                "pendientes": pendientes
            }
