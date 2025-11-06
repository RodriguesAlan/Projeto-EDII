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

echo [INFO] Atualizando o pip...
pip install --upgrade pip

echo [INFO] Instalando dependencias do projeto...
pip install -r backend\requirements_tree.txt

echo [INFO] Iniciando o backend na janela "Servidor Tree"...
start "Servidor Tree" cmd /k "cd /d \"%PROJECT_DIR%backend\" && call ..\venv\Scripts\activate && python app_tree.py"

echo [INFO] Abrindo a interface index_tree.html no navegador padrao...
start "" "%PROJECT_DIR%frontend\index_tree.html"

echo.
echo O servidor permanece ativo na janela "Servidor Tree". Para encerrar, feche a janela ou use CTRL+C nela.
echo Esta janela pode ser fechada apos verificar que tudo iniciou corretamente.
pause

endlocal
