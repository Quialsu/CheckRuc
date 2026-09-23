# Consulta_RUC_SUNAT (Versión v1.2.0_2026-09-23)

Aplicación modular y profesional en Python para consultar, procesar, consolidar y auditar información pública de empresas a partir de una lista de RUCs peruanos.

Diseñado para procesar desde unos pocos RUCs hasta **1,000, 10,000, 50,000+ RUCs** de forma rápida y segura mediante indexación local en SQLite.

---

## 📌 MATRIZ DE AUDITORÍA Y ESTADO DE REQUISITOS (v1.2.0)

| Requisito Téc. | Descripción | Estado Auditoría | Detalle de Verificación |
| :--- | :--- | :--- | :--- |
| **Padrón Seguro** | Actualización transaccional con respaldo en caso de archivo corrupto. | **IMPLEMENTADO Y VERIFICADO** | Flujo `IMPORTANDO` -> `VALIDADO` -> `ACTIVO`. Si la importación falla, la versión anterior sigue 100% activa. |
| **Cálculo SHA-256** | Huella digital real de archivos descargados/importados. | **IMPLEMENTADO Y VERIFICADO** | Implementado `hashlib.sha256()` por bloques de lectura. |
| **Domicilio Literal**| Preservar `Domicilio Fiscal Original` sin alteraciones. | **IMPLEMENTADO Y VERIFICADO** | Inmutabilidad garantizada. Los campos derivados de dirección se calculan por separado. |
| **Consulta Sin Padrón**| Evitar falsos `RUC NO ENCONTRADO` cuando no hay base activa. | **IMPLEMENTADO Y VERIFICADO** | Devuelve `ERROR TEMPORAL / Padrón No Importado` si la base relacional no tiene dataset activo. |
| **Aislamiento MOCK** | Evitar contaminación de MOCK en bases de datos de producción. | **IMPLEMENTADO Y VERIFICADO** | Clave compuesta (`ruc`, `fuente`, `dataset_ver`) en SQLite. |
| **Reporte 6 Hojas** | Hojas `RESULTADOS`, `PENDIENTES`, `ERRORES`, `RESUMEN`, `TRAZABILIDAD`, `FUENTES`. | **IMPLEMENTADO Y VERIFICADO** | Exportador `openpyxl` genera exactamente las 6 pestañas requeridas. |
| **SQL Chunking** | Paginación de consultas SQL para volúmenes de 50,000+ RUCs. | **IMPLEMENTADO Y VERIFICADO** | Consultas SQL paginadas en bloques de 800 parámetros para evitar límites de SQLite. |
| **Interfaz Web** | Interfaz local Streamlit interactiva con dashboard y botones de detener/reanudar. | **IMPLEMENTADO Y VERIFICADO** | `app.py` ejecutado vía `streamlit run app.py` o `INICIAR_APP.bat`. |
| **Descarga Auto** | Descarga automatizada vía API de Datos Abiertos. | **PARCIAL** | Importación manual y lectura de datasets en `data/cache/` completamente funcional. |

---

## ⚠️ AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD

> **IMPORTANTE:** Este proyecto es un software independiente de uso público y no oficial. **NO** está afiliado, ni patrocinado, ni respaldado por la Superintendencia Nacional de Aduanas y de Administración Tributaria (**SUNAT**) ni por ninguna entidad gubernamental de la República del Perú.

---

## 🚀 Guía de Instalación y Uso para Windows

### 1. Requisitos
* **Python 3.10** o superior instalado en Windows.
* Asegurarse de marcar **"Add Python to PATH"** durante la instalación de Python.

### 2. Ejecución Rápida
Hacer doble clic en el archivo **`INICIAR_APP.bat`**.

---

## 📄 Licencia

Este proyecto está distribuido bajo la licencia [MIT](LICENSE).
