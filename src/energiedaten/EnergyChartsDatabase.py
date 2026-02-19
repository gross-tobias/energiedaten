import mysql.connector
from mysql.connector import Error
from datetime import datetime
from EnergyChartsClient import *

class EnergyChartsDatabase:
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }

    def _createTables(self):
        commands = [
            """
            CREATE TABLE IF NOT EXISTS data_source (
                data_source_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                api_url VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS energy_source (
                energy_source_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS energy_data (
                energy_data_id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                value DOUBLE NOT NULL,
                energy_source_id INT,
                data_source_id INT,
                CONSTRAINT FOREIGN KEY (energy_source_id) REFERENCES energy_source (energy_source_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
                CONSTRAINT FOREIGN KEY (data_source_id) REFERENCES data_source (data_source_id) ON DELETE RESTRICT ON UPDATE RESTRICT
            )
            """,
            "INSERT INTO data_source (name, api_url) VALUES ('Energy Charts', 'https://api.energy-charts.info')",
            "INSERT INTO energy_source (name) VALUES ('Solar')",
            "INSERT INTO energy_source (name) VALUES ('Wind Onshore')",
            "INSERT INTO energy_source (name) VALUES ('Wind Offshore')",
        ]
        self._executeMany(commands)

    def _executeSelect(self, sql):
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error: {e}")

    def _executeBatch(self, sql, data):
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            cursor.executemany(sql, data)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error: {e}")

    def _executeMany(self, commands):
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            for cmd in commands:
                cursor.execute(cmd)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Database setup error: {e}")

    def saveEnergyData(self, energy_source, unix_times, values):
        sql = "SELECT data_source_id FROM data_source WHERE name = 'Energy Charts'"
        result = self._executeSelect(sql)
        if not result:
            return False
        data_source_id = result[0][0]
        
        sql = f"SELECT energy_source_id FROM energy_source WHERE name = '{energy_source}'"
        result = self._executeSelect(sql)
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
                        try:
                            dt = datetime.strptime(str(timestamp), '%m.%Y')
                        except ValueError:
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
            self._executeBatch(sql, records)
            print(f"{len(records)} Datensätze für {energy_source} gespeichert")
        return len(records) > 0

    def getEnergyData(self, energy_source=None, start_date=None, end_date=None):
        """Holt Energiedaten aus der Datenbank"""
        sql = """
            SELECT ed.timestamp, ed.value, es.name as energy_source_name
            FROM energy_data ed
            JOIN energy_source es ON ed.energy_source_id = es.energy_source_id
            WHERE 1=1
        """
        params = []
        
        if energy_source:
            sql += " AND es.name = %s"
            params.append(energy_source)
        
        if start_date:
            sql += " AND ed.timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            sql += " AND ed.timestamp <= %s"
            params.append(end_date)
        
        sql += " ORDER BY ed.timestamp ASC"
        
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # Konvertiere datetime-Objekte zu Strings
            for result in results:
                if isinstance(result['timestamp'], datetime):
                    result['timestamp'] = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                elif hasattr(result['timestamp'], 'isoformat'):
                    result['timestamp'] = result['timestamp'].isoformat()
            
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def getEnergySources(self):
        """Holt alle verfügbaren Energiequellen"""
        sql = "SELECT energy_source_id, name FROM energy_source ORDER BY name"
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error: {e}")
            return []

    def getLatestData(self, energy_source=None):
        """Holt die neuesten Daten für eine oder alle Energiequellen"""
        if energy_source:
            sql = """
                SELECT ed.timestamp, ed.value, es.name as energy_source_name
                FROM energy_data ed
                JOIN energy_source es ON ed.energy_source_id = es.energy_source_id
                WHERE es.name = %s
                ORDER BY ed.timestamp DESC
                LIMIT 1
            """
            params = [energy_source]
        else:
            sql = """
                SELECT ed.timestamp, ed.value, es.name as energy_source_name
                FROM energy_data ed
                JOIN energy_source es ON ed.energy_source_id = es.energy_source_id
                WHERE ed.timestamp = (SELECT MAX(timestamp) FROM energy_data)
            """
            params = []
        
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Error: {e}")
            return []