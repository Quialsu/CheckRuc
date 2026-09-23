# Consulta_RUC_SUNAT (Versión v1.0.0_2026-09-23)

Aplicación modular y profesional en Python para consultar, procesar, consolidar y auditar información pública de empresas a partir de una lista de RUCs peruanos.

Diseñado para procesar desde unos pocos RUCs hasta **1,000, 10,000, 50,000+ RUCs** de forma rápida y segura.

---

## 📌 ESTADO DE LAS FUNCIONALIDADES (v1.0.0)

### ✅ Funcionalidades Terminadas
- **Motor de Padrón Reducido SUNAT / Datos Abiertos**: Indexación SQLite local (`data/cache/`) para consultas hiper-rápidas en segundos.
- **Validación Estricta Módulo 11**: Algoritmo oficial de dígito verificador y comprobación de prefijos (`10`, `15`, `17`, `20`).
- **Preservación Inmutable de Domicilio Fiscal**: `Domicilio Fiscal Original` permanece exactamente igual al registro oficial.
- **Checkpoint Persistente en SQLite**: Persistencia independiente por combinación (RUC + Fuente + Versión Dataset) que evita la contaminación entre MOCK y REAL.
- **Trazabilidad Completa**: Registro de archivo origen, hoja y número de fila sin eliminar celdas vacías (`dropna` silencioso desactivado).
- **Interfaz Streamlit e Interfaz CLI (`main.py`)**: Panel de control con métricas en tiempo real, botones de detener/reanudar y descarga Excel.
- **Reporte Excel Multipestaña (`Consulta_RUC_SUNAT.xlsx`)**: Hojas `RESULTADOS`, `PENDIENTES`, `ERRORES`, `RESUMEN`, `TRAZABILIDAD` y `FUENTES`.

### ⏳ Funcionalidades Pendientes / En Desarrollo
- Descarga automatizada vía API de la Plataforma Nacional de Datos Abiertos para actualización de padrón con un solo clic.

### ⚠️ Funcionalidades No Verificadas / Limitaciones
- **Consulta Masiva Web SUNAT**: Marcada como **NO VERIFICADA PARA USO MASIVO** debido a controles anti-bot/CAPTCHA. La aplicación utiliza por defecto el Padrón Reducido Oficial.

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
