CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    gender VARCHAR(20),
    phone_number VARCHAR(20)
);

CREATE TABLE sleep_sessions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sleep_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sleep_sessions(id) ON DELETE CASCADE,
    heart_rate FLOAT,
    hrv FLOAT,
    spo2 FLOAT,
    sleep_stage VARCHAR(50),
    ahi FLOAT,
    total_events INTEGER,
    ai_severity VARCHAR(50),
    confirmed_severity VARCHAR(50),
    doctor_notes TEXT
);
