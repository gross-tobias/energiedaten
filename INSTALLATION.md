# Installation und Start

## Schnellstart

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 2. Datenbank starten
```bash
docker-compose up -d
```

### 3. Flask-Server starten
```bash
cd src/energiedaten
python app.py
```

### 4. Browser öffnen
```
http://localhost:5000
```

## Alternative: Startskript verwenden

Einfach `startfrontend.bat` doppelklicken (Windows) - das Skript installiert automatisch fehlende Abhängigkeiten und startet den Server.
