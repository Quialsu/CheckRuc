@echo off
chcp 65001 > nul
echo ====================================================
echo      INICIANDO SISTEMA DE CONSULTA RUC SUNAT
echo ====================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH del sistema.
    echo Por favor instala Python 3.10 o superior y asegurate de marcar "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/2] Verificando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Error al instalar o actualizar dependencias.
    pause
    exit /b 1
)

echo.
echo [2/2] Lanzando aplicacion Streamlit...
streamlit run app.py

pause
