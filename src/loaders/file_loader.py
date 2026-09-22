import os
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional

def load_ruc_file(file_path_or_buffer, file_name: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Loads an Excel (.xlsx, .xls) or CSV (.csv, .txt) file into a pandas DataFrame.
    Guarantees all columns are read as string / object dtype to avoid numeric distortion.
    DOES NOT silently drop empty rows.
    Returns: (df, list_of_column_names)
    """
    name = file_name or (file_path_or_buffer if isinstance(file_path_or_buffer, str) else getattr(file_path_or_buffer, 'name', 'file.csv'))
    ext = os.path.splitext(name)[1].lower()

    if ext in ['.xlsx', '.xls']:
        engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
        df = pd.read_excel(file_path_or_buffer, dtype=str, engine=engine)
    elif ext in ['.csv', '.txt']:
        try:
            df = pd.read_csv(file_path_or_buffer, dtype=str)
        except Exception:
            if hasattr(file_path_or_buffer, 'seek'):
                file_path_or_buffer.seek(0)
            df = pd.read_csv(file_path_or_buffer, dtype=str, encoding='latin-1', sep=None, engine='python')
    else:
        raise ValueError(f"Formato de archivo no soportado: {ext}. Utilice .xlsx, .xls, .csv o .txt.")

    df.columns = [str(col).strip() for col in df.columns]
    return df, list(df.columns)


def extract_ruc_records_with_trace(df: pd.DataFrame, column_name: str, file_name: str = "entrada") -> List[Dict[str, Any]]:
    """
    Extracts RUC values with full traceability per row (preserving empty cells instead of dropna).
    """
    if column_name not in df.columns:
        raise KeyError(f"La columna '{column_name}' no existe en el archivo. Columnas disponibles: {list(df.columns)}")

    records = []
    series = df[column_name]

    for idx, raw_val in enumerate(series):
        row_num = idx + 2  # 1-based header is row 1
        raw_str = str(raw_val) if pd.notna(raw_val) else ""
        records.append({
            "archivo_origen": file_name,
            "hoja_origen": "Hoja1",
            "fila_origen": row_num,
            "ruc_original": raw_str
        })

    return records


def auto_detect_ruc_column(columns: List[str]) -> Optional[str]:
    """
    Attempts to auto-detect which column contains RUC numbers based on standard header names.
    """
    candidates = ['ruc', 'num_ruc', 'numero_ruc', 'nro_ruc', 'ruc_num', 'ruc_numero', 'ruc_empresa']
    for col in columns:
        cleaned = str(col).lower().replace(' ', '_').replace('.', '')
        if cleaned in candidates or 'ruc' in cleaned:
            return col
    return columns[0] if columns else None
