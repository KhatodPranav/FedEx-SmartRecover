DROP DATABASE IF EXISTS fedex_dca;
CREATE DATABASE fedex_dca;
USE fedex_dca;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'agency') NOT NULL,
    agency_name VARCHAR(100),
    rating DECIMAL(3, 1) DEFAULT 5.0
);

CREATE TABLE cases (
    case_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    amount_due DECIMAL(10, 2),
    days_overdue INT,
    status VARCHAR(50) DEFAULT 'New',
    risk_score VARCHAR(20),
    assigned_to_agency_id INT,        
    FOREIGN KEY (assigned_to_agency_id) REFERENCES users(id)
);

CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    action_by_user_id INT,
    action_type VARCHAR(50), 
    description TEXT,           
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    FOREIGN KEY (action_by_user_id) REFERENCES users(id)
);

INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');

INSERT INTO users (username, password, role, agency_name, rating) 
VALUES ('agency1', 'agency123', 'agency', 'RapidRecover Inc', 4.5);