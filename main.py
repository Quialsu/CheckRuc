import sys
import argparse
import datetime
import logging
from pathlib import Path
from src.loaders.file_loader import load_ruc_file, extract_ruc_records_with_trace, auto_detect_ruc_column
from src.validators.ruc_validator import process_ruc_records
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import MockRUCSource, PadronReducidoSource, SunatWebSource
from src.processors.batch_processor import BatchProcessor
from src.exporters.excel_exporter import export_to_excel
from config import DEFAULT_EXCEL_OUTPUT

def main():
    parser = argparse.ArgumentParser(description="Consulta RUC SUNAT - CLI Batch Processor")
    parser.add_argument("--file", "-f", required=True, help="Ruta del archivo Excel o CSV de entrada")
    parser.add_argument("--column", "-c", help="Nombre de la columna que contiene los RUCs")
    parser.add_argument("--output", "-o", default=str(DEFAULT_EXCEL_OUTPUT), help="Ruta del archivo Excel de salida")
    parser.add_argument("--source", "-s", choices=["padron", "mock", "sunat_web"], default="padron", help="Fuente de consulta")
    parser.add_argument("--batch-size", type=int, default=1000, help="Tamaño de lote")

    args = parser.parse_args()

    print("====================================================")
    print("        CONSULTA RUC SUNAT - PROCESO CLI")
    print("====================================================")

    # 1. Load File
    print(f"[1/5] Cargando archivo: {args.file}...")
    df, cols = load_ruc_file(args.file)
    target_col = args.column or auto_detect_ruc_column(cols)
    if not target_col or target_col not in cols:
        print(f"[ERROR] Columna de RUC no encontrada. Columnas disponibles: {cols}")
        sys.exit(1)

    print(f"Columna seleccionada: '{target_col}'")
    raw_records = extract_ruc_records_with_trace(df, target_col, file_name=Path(args.file).name)

    # 2. Validate and Deduplicate
    print(f"[2/5] Validando y deduplicando RUCs...")
    val_res = process_ruc_records(raw_records)
    print(f"Total ingresados: {val_res['total_input']}")
    print(f"Únicos válidos: {val_res['unique_count']}")
    print(f"Vacíos / Inválidos: {len(val_res['invalid_records'])}")
    print(f"Duplicados omitidos: {len(val_res['duplicate_records'])}")

    if not val_res['valid_rucs']:
        print("[ERROR] No se encontraron RUCs válidos para procesar.")
        sys.exit(1)

    # 3. Source Selection
    if args.source == "padron":
        source = PadronReducidoSource()
    elif args.source == "sunat_web":
        source = SunatWebSource()
    else:
        source = MockRUCSource()

    chk_mgr = CheckpointManager()
    processor = BatchProcessor(source=source, checkpoint_mgr=chk_mgr, batch_size=args.batch_size)

    # 4. Processing
    print(f"[3/5] Procesando RUCs pendientes ({source.source_name} - {source.dataset_version})...")
    def print_progress(stats):
        pct = (stats['consultados'] + stats['no_encontrados']) / max(stats['total'], 1) * 100
        print(f"Progreso: {pct:.1f}% | Consultados: {stats['consultados']} | No Encontrados: {stats['no_encontrados']} | Errores: {stats['errores']} | Pendientes: {stats['pendientes']}")

    all_records = processor.process_rucs(val_res['valid_rucs'], progress_callback=print_progress)

    # 5. Export
    print(f"[4/5] Generando reporte Excel consolidado...")
    final_stats = chk_mgr.get_summary_stats(val_res['valid_rucs'], source.source_name, source.dataset_version)
    final_stats["total_input"] = val_res['total_input']
    final_stats["unique_count"] = val_res['unique_count']
    final_stats["fecha_hora"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_stats["fuente"] = source.source_name
    final_stats["dataset_ver"] = source.dataset_version

    out_file = export_to_excel(
        results=all_records,
        invalid_records=val_res['invalid_records'],
        duplicate_records=val_res['duplicate_records'],
        summary_stats=final_stats,
        all_input_rucs=val_res['valid_rucs'],
        output_path=args.output
    )

    print(f"[5/5] ¡Proceso completado exitosamente!")
    print(f"Archivo guardado en: {out_file}")

if __name__ == "__main__":
    main()
