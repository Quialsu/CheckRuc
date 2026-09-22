import re
import os
import datetime
import streamlit as st
import pandas as pd
from src.loaders.file_loader import load_ruc_file, extract_ruc_records_with_trace, auto_detect_ruc_column
from src.validators.ruc_validator import process_ruc_records
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import MockRUCSource, PadronReducidoSource, SunatWebSource
from src.processors.batch_processor import BatchProcessor
from src.exporters.excel_exporter import export_to_excel
from config import DEFAULT_EXCEL_OUTPUT, BATCH_SIZE

st.set_page_config(page_title="Consulta RUC SUNAT Masiva", page_icon="🏢", layout="wide")

st.title("🏢 Consulta RUC SUNAT - Procesamiento Masivo")
st.markdown("Sistema profesional para la consulta, validación, reanudación y consolidación masiva de RUCs peruanos.")

# Session state initialization
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

# Sidebar Configuration
st.sidebar.header("⚙️ Configuración")
source_selection = st.sidebar.selectbox(
    "Fuente de Consulta:",
    [
        "Padrón Reducido SUNAT (Oficial Masivo)",
        "Mock / Simulación (Pruebas Isoladas)",
        "SUNAT Web (Individual / Auxiliar)"
    ],
    index=0
)

batch_size_val = st.sidebar.number_input("Tamaño de Lote:", min_value=10, max_value=5000, value=1000, step=100)

st.sidebar.markdown("---")
st.sidebar.info("""
**Instrucciones:**
1. Seleccionar la modalidad de entrada.
2. Cargar archivo Excel/CSV o pegar RUCs.
3. Verificar validación y deduplicación.
4. Iniciar o reanudar el procesamiento.
5. Descargar el reporte `Consulta_RUC_SUNAT.xlsx`.
""")

# Input Mode
input_mode = st.radio(
    "Seleccionar Método de Entrada:",
    ["📁 Cargar Archivo Excel / CSV", "📋 Pegar RUCs Directamente"],
    horizontal=True
)

records = []

if input_mode == "📁 Cargar Archivo Excel / CSV":
    uploaded_file = st.file_uploader("Cargar archivo Excel (.xlsx, .xls) o CSV (.csv, .txt)", type=["xlsx", "xls", "csv", "txt"])
    if uploaded_file is not None:
        try:
            df, columns = load_ruc_file(uploaded_file, file_name=uploaded_file.name)
            st.success(f"Archivo cargado correctamente: `{uploaded_file.name}` ({len(df)} filas)")

            c1, c2 = st.columns([2, 1])
            with c1:
                detected_col = auto_detect_ruc_column(columns)
                selected_column = st.selectbox("Seleccionar Columna con RUC:", columns, index=columns.index(detected_col) if detected_col in columns else 0)
            with c2:
                st.write("")
                st.write("")
                st.info(f"Columna activa: `{selected_column}`")

            records = extract_ruc_records_with_trace(df, selected_column, file_name=uploaded_file.name)
        except Exception as e:
            st.error(f"Error cargando archivo: {str(e)}")

else:
    pasted_text = st.text_area(
        "Pegar RUCs aquí (separados por saltos de línea, comas o espacios):",
        height=150,
        placeholder="20131312955\n20100000001\n20500000002"
    )
    if pasted_text.strip():
        raw_list = [r.strip() for r in re.split(r'[\n\r,;\t\s]+', pasted_text) if r.strip()]
        for idx, val in enumerate(raw_list):
            records.append({
                "archivo_origen": "TextoPegadoDirecto",
                "hoja_origen": "TextoDirecto",
                "fila_origen": idx + 1,
                "ruc_original": val
            })

if records:
    try:
        val_res = process_ruc_records(records)

        st.subheader("📊 Resumen de Validación de Entrada")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL REGISTROS", val_res["total_input"])
        m2.metric("RUCs ÚNICOS VÁLIDOS", val_res["unique_count"])
        m3.metric("VACÍOS / INVÁLIDOS", len(val_res["invalid_records"]))
        m4.metric("DUPLICADOS OMITIDOS", len(val_res["duplicate_records"]))

        # Select Source Engine
        if "Padrón Reducido" in source_selection:
            source = PadronReducidoSource()
        elif "Mock" in source_selection:
            source = MockRUCSource()
        else:
            source = SunatWebSource()

        chk_mgr = CheckpointManager()
        stats = chk_mgr.get_summary_stats(val_res["valid_rucs"], source.source_name, source.dataset_version)

        st.subheader(f"📌 Estado del Checkpoint ({source.source_name} - {source.dataset_version})")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("TOTAL A PROCESAR", stats["total"])
        c2.metric("CONSULTADOS", stats["consultados"])
        c3.metric("NO ENCONTRADOS", stats["no_encontrados"])
        c4.metric("ERRORES", stats["errores"])
        c5.metric("PENDIENTES", stats["pendientes"])

        progress_val = (stats["consultados"] + stats["no_encontrados"]) / max(stats["total"], 1)
        st.progress(progress_val)

        col_btn1, col_btn2 = st.columns([1, 4])
        start_button = col_btn1.button("▶️ Iniciar / Reanudar Consulta", disabled=st.session_state.is_processing)
        stop_button = col_btn2.button("⏹️ Detener Proceso", disabled=not st.session_state.is_processing)

        if stop_button:
            st.session_state.stop_requested = True
            st.warning("Detención solicitada. Deteniendo proceso en el lote actual...")

        if start_button:
            st.session_state.is_processing = True
            st.session_state.stop_requested = False

            processor = BatchProcessor(source=source, checkpoint_mgr=chk_mgr, batch_size=batch_size_val)
            progress_bar = st.progress(progress_val)
            status_text = st.empty()

            def update_progress(current_stats):
                p = (current_stats["consultados"] + current_stats["no_encontrados"]) / max(current_stats["total"], 1)
                progress_bar.progress(p)
                status_text.text(f"Progreso: {p*100:.1f}% | Consultados: {current_stats['consultados']} | No Encontrados: {current_stats['no_encontrados']} | Pendientes: {current_stats['pendientes']}")

            def check_stop():
                return st.session_state.stop_requested

            all_records = processor.process_rucs(
                val_res["valid_rucs"],
                progress_callback=update_progress,
                stop_checker=check_stop
            )

            st.session_state.is_processing = False
            st.success("¡Procesamiento finalizado o pausado!")
            st.rerun()

        st.markdown("---")
        st.subheader("📥 Exportación de Resultados")
        if st.button("📄 Generar Reporte Excel Final (Consulta_RUC_SUNAT.xlsx)"):
            all_records = []
            with chk_mgr._get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in val_res["valid_rucs"])
                if placeholders:
                    cursor.execute(
                        f"SELECT * FROM ruc_consultas WHERE ruc IN ({placeholders}) AND fuente = ? AND dataset_ver = ?",
                        val_res["valid_rucs"] + [source.source_name, source.dataset_version]
                    )
                    all_records = [dict(row) for row in cursor.fetchall()]

            final_stats = chk_mgr.get_summary_stats(val_res["valid_rucs"], source.source_name, source.dataset_version)
            final_stats["total_input"] = val_res["total_input"]
            final_stats["unique_count"] = val_res["unique_count"]
            final_stats["fecha_hora"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            final_stats["fuente"] = source.source_name
            final_stats["dataset_ver"] = source.dataset_version

            export_file = export_to_excel(
                results=all_records,
                invalid_records=val_res["invalid_records"],
                duplicate_records=val_res["duplicate_records"],
                summary_stats=final_stats,
                all_input_rucs=val_res["valid_rucs"],
                output_path=str(DEFAULT_EXCEL_OUTPUT)
            )

            with open(export_file, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Consulta_RUC_SUNAT.xlsx",
                    data=f,
                    file_name="Consulta_RUC_SUNAT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Error procesando la solicitud: {str(e)}")
