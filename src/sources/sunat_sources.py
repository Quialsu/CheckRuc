import os
import sqlite3
import datetime
import urllib.request
import zipfile
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from config import PADRON_CACHE_DB
from src.parsers.address_parser import parse_fiscal_address

class BaseRUCSource(ABC):
    """
    Abstract Base Class for SUNAT RUC Data Sources.
    """
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def dataset_version(self) -> str:
        pass

    @abstractmethod
    def fetch_ruc(self, ruc: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def fetch_bulk_rucs(self, ruc_list: List[str]) -> List[Dict[str, Any]]:
        pass


class PadronReducidoSource(BaseRUCSource):
    """
    Official SUNAT Padrón Reducido Local Source (Indexed in SQLite).
    Handles 1k, 10k, and 50k+ RUC lookups locally in sub-seconds.
    """
    def __init__(self, db_path: str = str(PADRON_CACHE_DB)):
        self.db_path = db_path
        self._ensure_indexed()

    @property
    def source_name(self) -> str:
        return "SUNAT_PADRON_REDUCIDO_OFICIAL"

    @property
    def dataset_version(self) -> str:
        return "2026-Q3-OFICIAL"

    def _ensure_indexed(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS padron_reducido (
                ruc TEXT PRIMARY KEY,
                nombre_razon_social TEXT,
                estado TEXT,
                condicion TEXT,
                ubigeo TEXT,
                tipo_via TEXT,
                nombre_via TEXT,
                codigo_zona TEXT,
                tipo_zona TEXT,
                numero TEXT,
                interior TEXT,
                lote TEXT,
                departamento_int TEXT,
                manzana TEXT,
                kilometro TEXT
            )
        """)
        conn.commit()
        conn.close()

    def load_from_txt_file(self, txt_path: str):
        """
        Loads and indexes official Padrón Reducido raw TXT file into SQLite.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")

        with open(txt_path, 'r', encoding='latin-1', errors='replace') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 5 and parts[0].isdigit() and len(parts[0]) == 11:
                    cursor.execute("""
                        INSERT OR REPLACE INTO padron_reducido (
                            ruc, nombre_razon_social, estado, condicion, ubigeo,
                            tipo_via, nombre_via, codigo_zona, tipo_zona, numero,
                            interior, lote, departamento_int, manzana, kilometro
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        parts[0], parts[1], parts[2], parts[3], parts[4],
                        parts[5] if len(parts) > 5 else "",
                        parts[6] if len(parts) > 6 else "",
                        parts[7] if len(parts) > 7 else "",
                        parts[8] if len(parts) > 8 else "",
                        parts[9] if len(parts) > 9 else "",
                        parts[10] if len(parts) > 10 else "",
                        parts[11] if len(parts) > 11 else "",
                        parts[12] if len(parts) > 12 else "",
                        parts[13] if len(parts) > 13 else "",
                        parts[14] if len(parts) > 14 else ""
                    ))
        conn.commit()
        conn.close()

    def fetch_ruc(self, ruc: str) -> Dict[str, Any]:
        res = self.fetch_bulk_rucs([ruc])
        return res[0] if res else {}

    def fetch_bulk_rucs(self, ruc_list: List[str]) -> List[Dict[str, Any]]:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not ruc_list:
            return []

        results = []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        chunk_size = 900
        for i in range(0, len(ruc_list), chunk_size):
            chunk = ruc_list[i:i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            cursor.execute(f"SELECT * FROM padron_reducido WHERE ruc IN ({placeholders})", chunk)
            rows = cursor.fetchall()
            found_map = {row["ruc"]: dict(row) for row in rows}

            for ruc in chunk:
                if ruc in found_map:
                    row = found_map[ruc]
                    # Construct raw fiscal address string from official fields
                    raw_addr = f"{row['tipo_via']} {row['nombre_via']} {row['numero']} {row['tipo_zona']} {row['codigo_zona']}".strip()
                    parsed = parse_fiscal_address(raw_addr)

                    results.append({
                        "ruc": ruc,
                        "razon_social": row["nombre_razon_social"],
                        "fecha_inscripcion": "",  # Not present in Padron Reducido
                        "estado": row["estado"],
                        "condicion": row["condicion"],
                        "domicilio_fiscal_original": raw_addr,
                        "direccion": parsed["Dirección"],
                        "distrito": parsed["Distrito"],
                        "provincia": parsed["Provincia"],
                        "departamento": parsed["Departamento/Región"],
                        "ubigeo": row["ubigeo"],
                        "comercio_exterior": "",
                        "actividad_principal": "",
                        "actividades_secundarias": "",
                        "fuente": self.source_name,
                        "dataset_ver": self.dataset_version,
                        "fecha_consulta": now,
                        "estado_consulta": "CONSULTADO",
                        "error_tecnico": "",
                        "intentos": 1
                    })
                else:
                    results.append({
                        "ruc": ruc,
                        "razon_social": "",
                        "fecha_inscripcion": "",
                        "estado": "",
                        "condicion": "",
                        "domicilio_fiscal_original": "",
                        "direccion": "",
                        "distrito": "",
                        "provincia": "",
                        "departamento": "",
                        "ubigeo": "",
                        "comercio_exterior": "",
                        "actividad_principal": "",
                        "actividades_secundarias": "",
                        "fuente": self.source_name,
                        "dataset_ver": self.dataset_version,
                        "fecha_consulta": now,
                        "estado_consulta": "RUC NO ENCONTRADO",
                        "error_tecnico": "RUC no registrado en el Padrón Reducido SUNAT",
                        "intentos": 1
                    })
        conn.close()
        return results


class MockRUCSource(BaseRUCSource):
    """
    Isolated Mock Source for testing without polluting real production checkpoints.
    """
    @property
    def source_name(self) -> str:
        return "MOCK_SOURCE_TEST"

    @property
    def dataset_version(self) -> str:
        return "v1.0-MOCK"

    def fetch_ruc(self, ruc: str) -> Dict[str, Any]:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if ruc.endswith("000"):
            return {
                "ruc": ruc,
                "razon_social": "",
                "fecha_inscripcion": "",
                "estado": "",
                "condicion": "",
                "domicilio_fiscal_original": "",
                "direccion": "",
                "distrito": "",
                "provincia": "",
                "departamento": "",
                "ubigeo": "",
                "comercio_exterior": "",
                "actividad_principal": "",
                "actividades_secundarias": "",
                "fuente": self.source_name,
                "dataset_ver": self.dataset_version,
                "fecha_consulta": now,
                "estado_consulta": "RUC NO ENCONTRADO",
                "error_tecnico": "RUC no encontrado en mock",
                "intentos": 1
            }

        raw_addr = "AV. CANAVAL Y MOREYRA NRO. 150 LIMA - LIMA - SAN ISIDRO"
        parsed = parse_fiscal_address(raw_addr)

        return {
            "ruc": ruc,
            "razon_social": f"EMPRESA MOCK RUC {ruc} S.A.C.",
            "fecha_inscripcion": "02/01/2010",
            "estado": "ACTIVO",
            "condicion": "HABIDO",
            "domicilio_fiscal_original": parsed["Domicilio Fiscal Original"],
            "direccion": parsed["Dirección"],
            "distrito": parsed["Distrito"],
            "provincia": parsed["Provincia"],
            "departamento": parsed["Departamento/Región"],
            "ubigeo": parsed["Ubigeo"],
            "comercio_exterior": "IMPORTADOR/EXPORTADOR",
            "actividad_principal": "6201 - PROGRAMACION INFORMATICA",
            "actividades_secundarias": "6202 - CONSULTORIA INFORMATICA",
            "fuente": self.source_name,
            "dataset_ver": self.dataset_version,
            "fecha_consulta": now,
            "estado_consulta": "CONSULTADO",
            "error_tecnico": "",
            "intentos": 1
        }

    def fetch_bulk_rucs(self, ruc_list: List[str]) -> List[Dict[str, Any]]:
        return [self.fetch_ruc(r) for r in ruc_list]


class SunatWebSource(BaseRUCSource):
    """
    Individual SUNAT Web Query (Auxiliary / Single query only).
    """
    @property
    def source_name(self) -> str:
        return "SUNAT_WEB_INDIVIDUAL"

    @property
    def dataset_version(self) -> str:
        return "LIVE_WEB"

    def fetch_ruc(self, ruc: str) -> Dict[str, Any]:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "ruc": ruc,
            "razon_social": "",
            "fecha_inscripcion": "",
            "estado": "",
            "condicion": "",
            "domicilio_fiscal_original": "",
            "direccion": "",
            "distrito": "",
            "provincia": "",
            "departamento": "",
            "ubigeo": "",
            "comercio_exterior": "",
            "actividad_principal": "",
            "actividades_secundarias": "",
            "fuente": self.source_name,
            "dataset_ver": self.dataset_version,
            "fecha_consulta": now,
            "estado_consulta": "REQUIERE REVISIÓN",
            "error_tecnico": "Consulta masiva web no permitida por controles anti-bot/CAPTCHA. Utilice Padrón Reducido.",
            "intentos": 1
        }

    def fetch_bulk_rucs(self, ruc_list: List[str]) -> List[Dict[str, Any]]:
        return [self.fetch_ruc(r) for r in ruc_list]
