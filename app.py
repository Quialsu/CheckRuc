import streamlit as st
import pandas as pd
import datetime
import os
from src.loaders.file_loader import load_ruc_file, extract_ruc_column, auto_detect_ruc_column
from src.validators.ruc_validator import process_ruc_list
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import MockRUCSource, SunatWebSource
from src.processors.batch_processor import BatchProcessor
from src.exporters.excel_exporter import export_to_excel
from config import DEFAULT_EXCEL_OUTPUT, BATCH_SIZE

st.set_page_config(page_title="Consulta RUC SUNAT Masiva", page_icon="🏢", layout="wide")

st.title("🏢 Consulta RUC SUNAT - Procesamiento Masivo")
st.markdown("Sistema profesional para la consulta, validación, reanudación y consolidación de información empresarial de RUCs peruanos.")

# Session state initialization
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

# Sidebar Configuration
st.sidebar.header("⚙️ Configuración")
source_option = st.sidebar.selectbox(
    "Fuente de Consulta:",
    ["Mock / Simulación (Pruebas Rápida)", "SUNAT Web Oficial (Pública)"],
    index=0
)

batch_size_val = st.sidebar.number_input("Tamaño de Lote:", min_value=10, max_value=1000, value=100, step=10)

st.sidebar.markdown("---")
st.sidebar.info("""
**Instrucciones:**
1. Cargar archivo Excel (.xlsx, .xls) o CSV.
2. Seleccionar columna conteniendo RUCs.
3. Verificar la validación y deduplicación.
4. Iniciar o reanudar la consulta.
5. Descargar el reporte consolidado en Excel.
""")

# File Uploader
uploaded_file = st.file_uploader("Cargar archivo Excel o CSV", type=["xlsx", "xls", "csv", "txt"])

if uploaded_file is not None:
    try:
        df, columns = load_ruc_file(uploaded_file, file_name=uploaded_file.name)

        st.success(f"Archivo cargado correctamente: `{uploaded_file.name}` ({len(df)} filas)")

        col_select_1, col_select_2 = st.columns([2, 1])
        with col_select_1:
            detected_col = auto_detect_ruc_column(columns)
            selected_column = st.selectbox("Seleccionar Columna con RUC:", columns, index=columns.index(detected_col) if detected_col in columns else 0)

        with col_select_2:
            st.write("")
            st.write("")
            st.info(f"Columna activa: `{selected_column}`")

        # Extract and validate RUCs
        raw_rucs = extract_ruc_column(df, selected_column)
        val_res = process_ruc_list(raw_rucs)

        # Display Metrics
        st.subheader("📊 Resumen de Validación de Entrada")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL REGISTROS", val_res["total_input"])
        m2.metric("RUCs ÚNICOS VÁLIDOS", val_res["unique_count"])
        m3.metric("INVÁLIDOS", len(val_res["invalid_records"]))
        m4.metric("DUPLICADOS OMITIDOS", len(val_res["duplicate_records"]))

        # Checkpoint Status
        chk_mgr = CheckpointManager()
        stats = chk_mgr.get_summary_stats(val_res["valid_rucs"])

        st.subheader("📌 Estado del Checkpoint / Avance")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("TOTAL A PROCESAR", stats["total"])
        c2.metric("CONSULTADOS", stats["consultados"])
        c3.metric("NO ENCONTRADOS", stats["no_encontrados"])
        c4.metric("ERRORES", stats["errores"])
        c5.metric("PENDIENTES", stats["pendientes"])

        progress_val = (stats["consultados"] + stats["no_encontrados"]) / max(stats["total"], 1)
        st.progress(progress_val)

        # Controls
        col_btn1, col_btn2 = st.columns([1, 4])

        start_button = col_btn1.button("▶️ Iniciar / Reanudar Consulta", disabled=st.session_state.is_processing)
        stop_button = col_btn2.button("⏹️ Detener Proceso", disabled=not st.session_state.is_processing)

        if stop_button:
            st.session_state.stop_requested = True
            st.warning("Detención solicitada. Finalizando lote actual...")

        if start_button:
            st.session_state.is_processing = True
            st.session_state.stop_requested = False

            # Select Source
            if "SUNAT Web Oficial" in source_option:
                source = SunatWebSource()
                source_name = "SUNAT_WEB_OFICIAL"
            else:
                source = MockRUCSource()
                source_name = "MOCK_SOURCE (NO VERIFICADA EN VIVO)"

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
            st.success("¡Procesamiento finalizado o pausado exitosamente!")
            st.rerun()

        # Download Report
        st.markdown("---")
        st.subheader("📥 Exportación de Resultados")
        if st.button("📄 Generar Reporte Excel Final (Consulta_RUC_SUNAT.xlsx)"):
            all_records = []
            with chk_mgr._get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in val_res["valid_rucs"])
                if placeholders:
                    cursor.execute(f"SELECT * FROM ruc_consultas WHERE ruc IN ({placeholders})", val_res["valid_rucs"])
                    all_records = [dict(row) for row in cursor.fetchall()]

            final_stats = chk_mgr.get_summary_stats(val_res["valid_rucs"])
            final_stats["total_input"] = val_res["total_input"]
            final_stats["unique_count"] = val_res["unique_count"]
            final_stats["fecha_hora"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            final_stats["fuente"] = source_option

            export_file = export_to_excel(
                results=all_records,
                invalid_records=val_res["invalid_records"],
                duplicate_records=val_res["duplicate_records"],
                summary_stats=final_stats,
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
        st.error(f"Error procesando el archivo: {str(e)}")
