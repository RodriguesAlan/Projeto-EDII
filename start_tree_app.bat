@echo off
setlocal

REM Garante que o script execute a partir da pasta do projeto
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\venv"

if not exist "%VENV_DIR%\" (
    echo [INFO] Criando ambiente virtual na pasta backend...
    pushd "%BACKEND_DIR%"
    py -m venv venv
    popd
)

call "%VENV_DIR%\Scripts\activate"

echo [INFO] Atualizando o pip...
pip install --upgrade pip

echo [INFO] Instalando dependencias do projeto...
pip install -r "%BACKEND_DIR%\requirements_tree.txt"

echo [INFO] Iniciando o backend na janela "Servidor Tree"...
start "Servidor Tree" cmd /k "cd /d \"%BACKEND_DIR%\" && call venv\Scripts\activate && python app_tree.py"

echo [INFO] Abrindo a interface index_tree.html no navegador padrao...
start "" "%FRONTEND_DIR%\index_tree.html"

echo.
echo O servidor permanece ativo na janela "Servidor Tree". Para encerrar, feche a janela ou use CTRL+C nela.
echo Esta janela pode ser fechada apos verificar que tudo iniciou corretamente.
pause

endlocal
