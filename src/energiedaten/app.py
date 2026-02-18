from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from EnergyChartsDatabase import EnergyChartsDatabase
from EnergyChartsClient import EnergyChartsClient
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder='../../frontend', static_url_path='')
CORS(app)

# Datenbankverbindung - Anpassen nach Bedarf
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'energiedaten')
}

db = EnergyChartsDatabase(**DB_CONFIG)
client = EnergyChartsClient()

def _parse_date_arg(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None

@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/energy-sources')
def get_energy_sources():
    """Holt alle verfügbaren Energiequellen"""
    try:
        sources = db.getEnergySources()
        return jsonify(sources)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/energy-data')
def get_energy_data():
    """Holt Energiedaten mit optionalen Filtern"""
    try:
        energy_source = request.args.get('source')
        start_date_raw = request.args.get('start')
        end_date_raw = request.args.get('end')

        start_dt = _parse_date_arg(start_date_raw)
        end_dt = _parse_date_arg(end_date_raw)

        # If end date is given as YYYY-MM-DD, treat it as inclusive end-of-day
        if end_dt and isinstance(end_date_raw, str) and len(end_date_raw.strip()) == 10:
            end_dt = end_dt.replace(hour=23, minute=59, second=59)

        # Clamp to yesterday end-of-day (today may be incomplete)
        today = datetime.now()
        yesterday_eod = (today - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
        if end_dt and end_dt > yesterday_eod:
            end_dt = yesterday_eod
        if not end_dt and end_date_raw:
            end_dt = yesterday_eod
        
        data = db.getEnergyData(
            energy_source=energy_source,
            start_date=start_dt.strftime("%Y-%m-%d %H:%M:%S") if start_dt else None,
            end_date=end_dt.strftime("%Y-%m-%d %H:%M:%S") if end_dt else None
        )
        
        print(f"DEBUG: Gefundene Datensätze: {len(data)}")
        
        # Daten für Chart.js formatieren
        formatted_data = {}
        for record in data:
            source = record['energy_source_name']
            if source not in formatted_data:
                formatted_data[source] = {
                    'labels': [],
                    'values': []
                }
            
            timestamp = record['timestamp']
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    try:
                        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
                        except:
                            print(f"DEBUG: Konnte Timestamp nicht parsen: {timestamp}")
                            continue
            elif isinstance(timestamp, datetime):
                pass
            elif hasattr(timestamp, 'isoformat'):
                # MySQL datetime object
                timestamp = timestamp
            else:
                print(f"DEBUG: Unbekannter Timestamp-Typ: {type(timestamp)}")
                continue
            
            formatted_data[source]['labels'].append(timestamp.strftime('%Y-%m-%d'))
            formatted_data[source]['values'].append(float(record['value']))
        
        print(f"DEBUG: Formatierte Daten: {len(formatted_data)} Quellen")
        return jsonify(formatted_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest-data')
def get_latest_data():
    """Holt die neuesten Daten"""
    try:
        energy_source = request.args.get('source')
        data = db.getLatestData(energy_source=energy_source)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/count')
def debug_count():
    """Debug-Endpoint: Zählt Datensätze in der Datenbank"""
    try:
        sql = "SELECT COUNT(*) as count FROM energy_data"
        result = db._executeSelect(sql)
        count = result[0][0] if result else 0
        
        sql = "SELECT es.name, COUNT(*) as count FROM energy_data ed JOIN energy_source es ON ed.energy_source_id = es.energy_source_id GROUP BY es.name"
        by_source = db._executeSelect(sql)
        
        return jsonify({
            'total_count': count,
            'by_source': {row['name']: row['count'] for row in by_source} if by_source else {}
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def _savePowerData(data, energy_source):
    """Speichert Power-Daten (GW) in der Datenbank"""
    if not data:
        print(f"DEBUG: Keine Daten für {energy_source}")
        return False
    
    print(f"DEBUG: Datenformat für {energy_source}: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
    
    # Prüfe verschiedene Datenformate der API
    unix_times = None
    values = None
    
    if isinstance(data, dict):
        if "unix_seconds" in data and "data" in data:
            unix_times = data["unix_seconds"]
            for type in data['production_types']:
                if type['name'] == energy_source:
                    values = type["data"]
        elif "unix_timestamps" in data and "data" in data:
            unix_times = data["unix_timestamps"]
            values = data["data"]
        elif "timestamps" in data and "data" in data:
            unix_times = data["timestamps"]
            values = data["data"]
        elif "days" in data and "data" in data:
            # Fallback auf Daily Average Format
            print(f"DEBUG: Verwende Daily Average Format für {energy_source}")
            db.saveDailyAverage(data, energy_source)
            return True
    elif isinstance(data, list) and len(data) > 0:
        # Alternative Format
        unix_times = [item.get("timestamp", item.get("unix_seconds")) for item in data]
        values = [item.get("value", item.get("data")) for item in data]
    
    if not unix_times or not values:
        print(f"DEBUG: Keine Zeitstempel oder Werte für {energy_source}")
        # Versuche Daily Average Format als Fallback
        if isinstance(data, dict) and "days" in data:
            print(f"DEBUG: Versuche Daily Average Format für {energy_source}")
            db.saveDailyAverage(data, energy_source)
            return True
        return False
    
    try:
        sql = "SELECT data_source_id FROM data_source WHERE name = 'Energy Charts'"
        result = db._executeSelect(sql)
        if not result:
            return False
        data_source_id = result[0][0]
        
        sql = f"SELECT energy_source_id FROM energy_source WHERE name = '{energy_source}'"
        result = db._executeSelect(sql)
        if not result:
            return False
        energy_source_id = result[0][0]
        
        records = []
        for timestamp, val in zip(unix_times, values):
            if val is not None and val != 0:
                try:
                    if isinstance(timestamp, (int, float)):
                        dt = datetime.fromtimestamp(timestamp)
                    else:
                        dt = datetime.fromisoformat(str(timestamp))
                    records.append((
                        dt,
                        float(val),
                        energy_source_id,
                        data_source_id
                    ))
                except Exception as e:
                    print(f"Fehler beim Parsen von Timestamp: {e}")
                    continue
        
        if records:
            sql = "INSERT IGNORE INTO energy_data (timestamp, value, energy_source_id, data_source_id) VALUES (%s, %s, %s, %s)"
            db._executeBatch(sql, records)
            print(f"{len(records)} Datensätze für {energy_source} gespeichert")
        return len(records) > 0
    except Exception as e:
        print(f"Error saving power data for {energy_source}: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/api/fetch-solar')
def fetch_solar():
    """Lädt Solar-Daten (kWh) von der API und speichert sie in der DB"""
    try:
        data = client.getPublicPower(country="de", subtype="Solar")
        success = _savePowerData(data, "Solar")
        if success:
            return jsonify({'success': True, 'message': 'Solar-Daten erfolgreich geladen'})
        else:
            return jsonify({'error': 'Keine Daten erhalten'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-wind-onshore')
def fetch_wind_onshore():
    """Lädt Wind Onshore-Daten (kWh) von der API und speichert sie in der DB"""
    try:
        data = client.getPublicPower(country="de", subtype="Wind_onshore")
        success = _savePowerData(data, "Wind Onshore")
        if success:
            return jsonify({'success': True, 'message': 'Wind Onshore-Daten erfolgreich geladen'})
        else:
            return jsonify({'error': 'Keine Daten erhalten'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-wind-offshore')
def fetch_wind_offshore():
    """Lädt Wind Offshore-Daten (kWh) von der API und speichert sie in der DB"""
    try:
        data = client.getPublicPower(country="de", subtype="Wind_offshore")
        success = _savePowerData(data, "Wind Offshore")
        if success:
            return jsonify({'success': True, 'message': 'Wind Offshore-Daten erfolgreich geladen'})
        else:
            return jsonify({'error': 'Keine Daten erhalten'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-all')
def fetch_all():
    """Lädt alle verfügbaren Daten (kWh) von der API"""
    try:
        results = {}
        
        # Solar - versuche verschiedene API-Endpunkte
        try:
            print("DEBUG: Lade Solar-Daten...")
            # Versuche zuerst getPublicPower
            try:
                data = client.getPublicPower(country="de", subtype="Solar")
                print(f"DEBUG: getPublicPower Solar Antwort: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                success = _savePowerData(data, "Solar")
            except Exception as e1:
                print(f"DEBUG: getPublicPower fehlgeschlagen: {e1}")
                success = False
            
            if not success:
                # Fallback: verwende Share-Daten
                print("DEBUG: Verwende SolarShareDailyAvg als Fallback...")
                data = client.getSolarShareDailyAvg()
                print(f"DEBUG: SolarShareDailyAvg Antwort: {type(data)}, Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                success = db.saveDailyAverage(data, "Solar")
            results['solar'] = 'success' if success else 'no data'
        except Exception as e:
            print(f"Error fetching solar: {e}")
            import traceback
            traceback.print_exc()
            results['solar'] = str(e)
        
        # Wind Onshore
        try:
            print("DEBUG: Lade Wind Onshore-Daten...")
            try:
                data = client.getPublicPower(country="de", subtype="Wind_onshore")
                success = _savePowerData(data, "Wind Onshore")
            except Exception as e1:
                print(f"DEBUG: getPublicPower Wind Onshore fehlgeschlagen: {e1}")
                success = False
            
            if not success:
                print("DEBUG: Verwende WindOnshoreShareDailyAvg als Fallback...")
                data = client.getWindOnshoreShareDailyAvg()
                success = db.saveDailyAverage(data, "Wind Onshore")
            results['wind_onshore'] = 'success' if success else 'no data'
        except Exception as e:
            print(f"Error fetching wind onshore: {e}")
            import traceback
            traceback.print_exc()
            results['wind_onshore'] = str(e)
        
        # Wind Offshore
        try:
            print("DEBUG: Lade Wind Offshore-Daten...")
            try:
                data = client.getPublicPower(country="de", subtype="Wind_offshore")
                success = _savePowerData(data, "Wind Offshore")
            except Exception as e1:
                print(f"DEBUG: getPublicPower Wind Offshore fehlgeschlagen: {e1}")
                success = False
            
            if not success:
                print("DEBUG: Verwende WindOffshoreShareDailyAvg als Fallback...")
                data = client.getWindOffshoreShareDailyAvg()
                success = db.saveDailyAverage(data, "Wind Offshore")
            results['wind_offshore'] = 'success' if success else 'no data'
        except Exception as e:
            print(f"Error fetching wind offshore: {e}")
            import traceback
            traceback.print_exc()
            results['wind_offshore'] = str(e)
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
