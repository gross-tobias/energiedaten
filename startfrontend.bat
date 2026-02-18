@echo off
echo Starte Energiedaten Frontend...
echo.

cd /d "%~dp0"
cd src\energiedaten

REM --- Lade .env (Docker MySQL) und mappe auf App-Variablen ---
if exist "..\..\.env" (
  for /f "usebackq tokens=1,* delims== eol=#" %%A in ("..\..\.env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)

if defined MYSQL_DATABASE set "DB_NAME=%MYSQL_DATABASE%"
if defined MYSQL_ROOT_PASSWORD set "DB_PASSWORD=%MYSQL_ROOT_PASSWORD%"
if not defined DB_HOST set "DB_HOST=127.0.0.1"
if not defined DB_USER set "DB_USER=root"

echo Pruefe Python-Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH!
    pause
    exit /b 1
)

echo Pruefe Abhaengigkeiten...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installiere Python-Abhaengigkeiten...
    cd ..\..
    pip install -r requirements.txt
    cd src\energiedaten
)

echo.
echo Starte Flask-Server...
echo Frontend erreichbar unter: http://localhost:5000
echo.
echo Zum Beenden: Strg+C druecken
echo.

python app.py

pause
