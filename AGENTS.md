# Guía para Agentes - Consulta RUC SUNAT

Este repositorio alberga la aplicación para consulta, procesamiento, consolidación y auditoría masiva de RUCs de SUNAT (Perú).

## Arquitectura del Proyecto

```
consulta_ruc_sunat/
├── app.py                     # Interfaz de usuario con Streamlit
├── main.py                    # Interfaz de Línea de Comandos (CLI)
├── config.py                  # Parámetros y rutas globales del sistema
├── requirements.txt           # Dependencias de Python
├── INICIAR_APP.bat            # Lanzador para entornos Windows
├── input/                     # Archivos de entrada del usuario
│   └── README_INPUT.txt
├── output/                    # Resultados, logs y exportaciones
│   ├── consultas/
│   ├── exports/
│   └── logs/
├── data/                      # Base de datos local SQLite y caché
│   ├── cache/
│   └── checkpoints/
├── src/                       # Módulos del sistema
│   ├── loaders/               # Carga de archivos Excel/CSV
│   ├── sources/               # Fuentes de datos (SUNAT Web, Padrón, Mock)
│   ├── processors/            # Procesamiento en lotes
│   ├── parsers/               # Extracción y desglose de domicilios
│   ├── validators/            # Validación estricta y algoritmo RUC
│   ├── exporters/             # Generación de Excel consolidado
│   ├── checkpoint/            # Gestión de persistencia SQLite
│   └── utils/                 # Utilidades varias y logging
└── tests/                     # Pruebas unitarias e integración con Pytest
```

## Reglas y Directrices Principales

1. **Domicilio Fiscal Original**:
   - `Domicilio Fiscal Original` NUNCA debe ser alterado, limpiado ni recortado. Debe guardarse tal cual proviene de la fuente oficial.
   - Las partes de la dirección (`Dirección`, `Distrito`, `Provincia`, `Departamento/Región`, `Ubigeo`) se deben guardar en columnas derivadas separadas.

2. **Columnas de Salida Obligatorias en la Hoja `RESULTADOS`**:
   - `RUC`
   - `Razón Social`
   - `Fecha Inscripción`
   - `Estado`
   - `Condición`
   - `Domicilio Fiscal Original`
   - `Dirección`
   - `Distrito`
   - `Provincia`
   - `Departamento/Región`
   - `Ubigeo`
   - `Comercio Exterior`
   - `Actividad Económica Principal`
   - `Actividades Económicas`
   - `Fuente`
   - `Fecha Consulta`
   - `Estado Consulta`

3. **Formato RUC**:
   - Debe manejarse siempre como texto (string de 11 caracteres) con ceros a la izquierda preservados.
   - En Excel debe configurarse explícitamente como formato de texto `@`.

4. **Checkpoint y Reanudación**:
   - La base de datos local SQLite en `data/checkpoints/consultas.db` garantiza que el sistema pueda detenerse y reanudarse sin perder progreso ni reconsultar registros procesados.

5. **Cumplimiento y Fuentes**:
   - Priorizar mecanismos oficiales públicos y/o datos abiertos.
   - Manejar reintentos con exponencial backoff para fallos temporales de red.
