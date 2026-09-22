# Sistema de Consulta Masiva RUC SUNAT (Perú)

Aplicación modular y profesional en Python para consultar, procesar, consolidar y auditar información pública de empresas a partir de una lista de RUCs peruanos.

Disenado para procesar desde unos pocos RUCs hasta **1,000, 10,000, 50,000+ RUCs** de forma rápida y segura.

---

## ⚠️ AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD

> **IMPORTANTE:** Este proyecto es un software independiente de uso público y no oficial. **NO** está afiliado, ni patrocinado, ni respaldado por la Superintendencia Nacional de Aduanas y de Administración Tributaria (**SUNAT**) ni por ninguna entidad gubernamental de la República del Perú. Toda la información tributaria y empresarial proviene de la consulta de fuentes públicas de datos abiertos autorizados.

---

## 🚀 Guía de Instalación y Uso para Windows

### 1. Requisitos
* **Python 3.10** o superior instalado en Windows.
* Asegurarse de marcar **"Add Python to PATH"** durante la instalación de Python.

### 2. Ejecución Rápida
Hacer doble clic en el archivo **`INICIAR_APP.bat`**.

El script automáticamente:
1. Verificará Python en el sistema.
2. Instalará/actualizará las dependencias desde `requirements.txt`.
3. Abrirá la aplicación web local en su navegador predeterminado (`http://localhost:8501`).

---

## 📊 Arquitectura y Fuentes de Consulta

El motor principal utiliza el **Padrón Reducido SUNAT / Datos Abiertos oficial**:
* **Indexación local en SQLite** (`data/cache/`) que permite resolver 50,000+ consultas en segundos.
* **Checkpoint permanente** en `data/checkpoints/consultas.db` para reanudar automáticamente ante interrupciones.
* **Aislamiento completo:** Las ejecuciones de prueba MOCK están 100% aisladas de la base de datos de producción REAL.

---

## 📄 Licencia

Este proyecto está distribuido bajo la licencia [MIT](LICENSE).
