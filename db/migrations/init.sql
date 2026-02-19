-- --------------------------------------------------
-- Create database
-- --------------------------------------------------
CREATE DATABASE IF NOT EXISTS energydata_db;
USE energydata_db;

-- --------------------------------------------------
-- Table: data_source
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS data_source (
    data_source_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_url VARCHAR(255)
);

-- --------------------------------------------------
-- Table: energy_source
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_source (
    energy_source_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- --------------------------------------------------
-- Table: energy_data
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_data (
    energy_data_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    value DOUBLE NOT NULL,
    energy_source_id INT,
    data_source_id INT,
    CONSTRAINT FOREIGN KEY (energy_source_id) REFERENCES energy_source (energy_source_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT FOREIGN KEY (data_source_id) REFERENCES data_source (data_source_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- --------------------------------------------------
-- Insert initial data
-- --------------------------------------------------
INSERT INTO data_source (name, api_url)
VALUES ('Energy Charts', 'https://api.energy-charts.info');

INSERT INTO energy_source (name)
VALUES ('Solar');

INSERT INTO energy_source (name)
VALUES ('Wind Onshore');

INSERT INTO energy_source (name)
VALUES ('Wind Offshore');

INSERT INTO energy_source (name)
VALUES ('Biomass');