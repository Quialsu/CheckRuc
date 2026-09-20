# Sistema de Consulta RUC SUNAT (Perú)

Aplicación modular, profesional e interactiva desarrollada en Python para la consulta, validación, reanudación automática y consolidación masiva de RUCs de SUNAT (Perú).

Designed to handle batch sizes from a few RUCs to 50,000+ records safely using SQLite checkpoints.

---

## 🚀 Guía de Instalación y Uso para Windows

### 1. Requisitos Previos
* Tener instalado **Python 3.10** o superior en Windows.
* Durante la instalación de Python, asegurarse de marcar la casilla **"Add Python to PATH"**.

### 2. Ejecución Rápida (Recomendado)
Hacer doble clic en el archivo `INICIAR_APP.bat`.
El ejecutable automáticamente:
1. Verificará Python.
2. Instalará/actualizará las librerías necesarias (`requirements.txt`).
3. Iniciará la interfaz web de Streamlit en su navegador predeterminado (`http://localhost:8501`).

### 3. Ejecución Manual por Consola

#### A. Interfaz Gráfica (Streamlit)
```cmd
pip install -r requirements.txt
streamlit run app.py
```

#### B. Interfaz de Línea de Comandos (CLI)
Para ejecuciones desatendidas o programadas por lotes:
```cmd
python main.py --file input/mis_rucs.xlsx --source mock --batch-size 100
```

---

## 📊 Características y Funcionalidades

1. **Validación Estricta de RUC**:
   - Algoritmo oficial Módulo 11 para dígito verificador.
   - Comprobación de prefijos válidos (`10`, `15`, `17`, `20`).
   - Deduplicación automática registrando duplicados e inválidos por separado.

2. **Garantía de Domicilio Fiscal**:
   - `Domicilio Fiscal Original` permanece **EXACTAMENTE** como se recibe de la fuente pública sin ninguna alteración.
   - Desglose derivado independiente: Dirección, Distrito, Provincia, Departamento y Ubigeo.

3. **Checkpoint y Reanudación Automática**:
   - Almacenamiento local persistente mediante SQLite en `data/checkpoints/consultas.db`.
   - Permite detener la aplicación en cualquier momento y reanudar posteriormente sin volver a consultar RUCs ya procesados.

4. **Reporte Excel Multipestaña (`Consulta_RUC_SUNAT.xlsx`)**:
   - `RESULTADOS`: Las 17 columnas obligatorias con formato explícito de texto para el RUC.
   - `PENDIENTES`: Registros pendientes de consulta.
   - `ERRORES`: Motivos técnicos, RUCs inválidos y duplicados omitidos.
   - `RESUMEN`: Métricas generales, totalizadores, marcas de tiempo y fuentes utilizadas.

---

## 📁 Estructura del Proyecto

```
consulta_ruc_sunat/
├── app.py                     # Interfaz web de Streamlit
├── main.py                    # Interfaz CLI
├── config.py                  # Configuración global
├── requirements.txt           # Dependencias de Python
├── INICIAR_APP.bat            # Lanzador para Windows
├── AGENTS.md                  # Especificaciones técnicas para agentes
├── input/                     # Archivos de entrada
├── output/                    # Exportaciones Excel y logs
└── tests/                     # Pruebas unitarias automatizadas
```
