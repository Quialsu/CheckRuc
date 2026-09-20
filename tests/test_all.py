import os
import pytest
import pandas as pd
from src.validators.ruc_validator import validate_ruc, validate_ruc_checksum, process_ruc_list
from src.loaders.file_loader import load_ruc_file, extract_ruc_column, auto_detect_ruc_column
from src.parsers.address_parser import parse_fiscal_address
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import MockRUCSource
from src.processors.batch_processor import BatchProcessor
from src.exporters.excel_exporter import export_to_excel


def test_ruc_checksum():
    # Valid SUNAT RUC
    assert validate_ruc_checksum("20131312955") is True
    # Invalid Checksum
    assert validate_ruc_checksum("20131312950") is False
    # Non-digit string
    assert validate_ruc_checksum("2013131295A") is False


def test_validate_ruc():
    # Valid
    is_valid, clean, err = validate_ruc("20131312955")
    assert is_valid is True
    assert clean == "20131312955"
    assert err == ""

    # Invalid prefix
    is_valid, clean, err = validate_ruc("12345678901")
    assert is_valid is False
    assert "Prefijo" in err

    # Short length
    is_valid, clean, err = validate_ruc("20131")
    assert is_valid is False
    assert "11" in err


def test_process_ruc_list():
    raw_list = ["20131312955", "20131312955", "12345678901", 20131312955]
    res = process_ruc_list(raw_list)
    assert res["total_input"] == 4
    assert res["unique_count"] == 1
    assert len(res["invalid_records"]) == 1
    assert len(res["duplicate_records"]) == 2


def test_file_loader_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    df_sample = pd.DataFrame({"NRO_RUC": ["20131312955", "00100000001"]})
    df_sample.to_csv(csv_file, index=False)

    df, cols = load_ruc_file(str(csv_file))
    assert "NRO_RUC" in cols
    auto_col = auto_detect_ruc_column(cols)
    assert auto_col == "NRO_RUC"

    extracted = extract_ruc_column(df, auto_col)
    assert extracted == ["20131312955", "00100000001"]


def test_address_parser():
    raw_addr = "AV. CANAVAL Y MOREYRA NRO. 150 LIMA - LIMA - SAN ISIDRO"
    parsed = parse_fiscal_address(raw_addr)

    # Check absolute preservation of Domicilio Fiscal Original
    assert parsed["Domicilio Fiscal Original"] == raw_addr
    assert parsed["Distrito"] == "SAN ISIDRO"
    assert parsed["Provincia"] == "LIMA"
    assert parsed["Departamento/Región"] == "LIMA"
    assert parsed["Ubigeo"] == "150131"


def test_checkpoint_and_resume(tmp_path):
    db_file = tmp_path / "test_chk.db"
    chk = CheckpointManager(db_path=str(db_file))

    # Save 1 record
    chk.save_record({"ruc": "20131312955", "razon_social": "SUNAT", "estado_consulta": "CONSULTADO"})

    # Verify retrieval
    record = chk.get_record("20131312955")
    assert record["razon_social"] == "SUNAT"
    assert record["estado_consulta"] == "CONSULTADO"

    # Verify summary stats
    stats = chk.get_summary_stats(["20131312955", "20100000001"])
    assert stats["total"] == 2
    assert stats["consultados"] == 1
    assert stats["pendientes"] == 1


def test_batch_processor_integration(tmp_path):
    db_file = tmp_path / "proc_chk.db"
    chk = CheckpointManager(db_path=str(db_file))
    processor = BatchProcessor(source=MockRUCSource(), checkpoint_mgr=chk, batch_size=2)

    rucs = ["20131312955", "20100000001"]
    records = processor.process_rucs(rucs)

    assert len(records) == 2
    processed = chk.get_processed_rucs()
    assert "20131312955" in processed


def test_excel_export(tmp_path):
    out_file = tmp_path / "Consulta_RUC_SUNAT.xlsx"
    results = [{
        "ruc": "20131312955",
        "razon_social": "SUNAT",
        "fecha_inscripcion": "02/01/2010",
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "domicilio_fiscal_original": "AV. CANAVAL Y MOREYRA NRO. 150 LIMA - LIMA - SAN ISIDRO",
        "direccion": "AV. CANAVAL Y MOREYRA NRO. 150",
        "distrito": "SAN ISIDRO",
        "provincia": "LIMA",
        "departamento": "LIMA",
        "ubigeo": "150131",
        "comercio_exterior": "IMPORTADOR/EXPORTADOR",
        "actividad_principal": "6201 - PROGRAMACION INFORMATICA",
        "actividades_secundarias": "6202 - CONSULTORIA INFORMATICA",
        "fuente": "MOCK",
        "fecha_consulta": "2026-09-20",
        "estado_consulta": "CONSULTADO"
    }]

    stats = {
        "total_input": 1,
        "unique_count": 1,
        "consultados": 1,
        "no_encontrados": 0,
        "errores": 0,
        "pendientes": 0,
        "fecha_hora": "2026-09-20",
        "fuente": "MOCK"
    }

    generated_path = export_to_excel(results, [], [], stats, output_path=str(out_file))
    assert os.path.exists(generated_path)
