@echo off
setlocal

REM Garante que o script execute a partir da pasta do projeto
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist venv (
    echo [INFO] Criando ambiente virtual...
    py -m venv venv
)

call venv\Scripts\activate

pip install --upgrade pip >nul
pip install -r backend\requirements_tree.txt

REM Inicia o backend em uma nova janela
start "Servidor Tree" cmd /c "cd /d \"%PROJECT_DIR%backend\" && python app_tree.py"

REM Aguarda alguns segundos para garantir que o servidor esteja pronto
timeout /t 3 /nobreak >nul

REM Abre a interface web index_tree no navegador padrão
start "" "http://127.0.0.1:5000/index_tree"

endlocal
