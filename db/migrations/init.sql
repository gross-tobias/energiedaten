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
    name VARCHAR(100) NOT NULL,
    api_url VARCHAR(255) NOT NULL
);

-- --------------------------------------------------
-- Table: energy_source
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_source (
    energy_source_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_renewable BOOLEAN NOT NULL
);

-- --------------------------------------------------
-- Table: energy_data
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_data (
    energy_data_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    value DECIMAL(10,3) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    energy_source_id INT NOT NULL,
    data_source_id INT NOT NULL,
    -- Foreign Key Constraints
    CONSTRAINT fk_energy_source
        FOREIGN KEY (energy_source_id) REFERENCES energy_source(energy_source_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source(data_source_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
