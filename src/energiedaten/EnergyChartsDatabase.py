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
        self._createTables()

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
            "INSERT INTO energy_source (name) VALUES ('Wind Offshore')"
        ]
        self._executeMany(commands)

    def saveDailyAverage(self, data, energy_source):
        if not data or "days" not in data:
           return

        sql = "SELECT data_source_id FROM data_source WHERE name = 'Energy Charts'"
        data_source_id = self._executeSelect(sql)[0][0]

        sql = f"SELECT energy_source_id FROM energy_source WHERE name = '{energy_source}'"
        energy_source_id = self._executeSelect(sql)[0][0]

        records = []
        for day, val in zip(data["days"], data["data"]):
            if val is not None:
                records.append((
                    datetime.strptime(day, "%d.%m.%Y"),
                    val,
                    energy_source_id,
                    data_source_id))

        sql = "INSERT IGNORE INTO energy_data (timestamp, value, energy_source_id, data_source_id) VALUES (%s, %s, %s, %s)"
        self._executeBatch(sql, records)

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
