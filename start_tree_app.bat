@echo off
setlocal

REM Garante que o script execute a partir da pasta do projeto
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\venv"

echo [INFO] Acessando a pasta backend...
pushd "%BACKEND_DIR%"

if not exist "%VENV_DIR%\" (
    echo [INFO] Criando ambiente virtual na pasta backend...
    py -m venv venv
)

call "%VENV_DIR%\Scripts\activate"

echo [INFO] Atualizando o pip...
python -m pip install --upgrade pip

echo [INFO] Instalando dependencias do projeto...
python -m pip install -r requirements_tree.txt

echo [INFO] Abrindo a interface index_tree.html no navegador padrao...
start "" "%FRONTEND_DIR%\index_tree.html"

echo [INFO] Iniciando o backend (use CTRL+C para encerrar)...
python app_tree.py

echo.
echo Servidor finalizado. Pressione qualquer tecla para sair.
pause >nul

popd
endlocal
