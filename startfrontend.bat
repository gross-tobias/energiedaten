@echo off
echo Starte Energiedaten Frontend...
echo.

cd /d "%~dp0"
cd src\energiedaten

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
