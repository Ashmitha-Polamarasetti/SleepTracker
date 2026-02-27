-> Sleep Apnea Detection System
-> Full-Stack AI Healthcare Platform | FastAPI + TensorFlow + Docker

An end-to-end AI-powered system that detects sleep apnea from ECG signals and provides structured medical insights through a secure web dashboard.

---

-> Project Highlights

-  Deep Learning model trained on PhysioNet Apnea-ECG dataset
-  Computes clinical metrics: HR, HRV, AHI, Severity Index
-  ~93% model accuracy
-  Role-based authentication (Doctor / Patient)
-  Fully containerized using Docker Compose
-  PostgreSQL-backed persistent storage
-  REST-based microservices architecture

---

-> System Architecture

Doctor Upload → Backend API → AI Inference Service → PostgreSQL → Dashboard

-> Microservices:
- sleep_backend – FastAPI API & authentication
- sleep_ai – TensorFlow inference service
- sleep_db – PostgreSQL database

---

-> AI Model Details

- 1D Convolutional Neural Network (CNN)
- Binary classification (Apnea / Normal)
- Optimizer: Adam
- Loss: Binary Crossentropy
- Accuracy: ~93%

-> Clinical Metrics Computed:
- Heart Rate (HR)
- Heart Rate Variability (HRV - SDNN)
- Apnea-Hypopnea Index (AHI)
- Severity Classification
- Total Apnea Events
- Sleep Stage Estimation

---

-> Severity Classification

| AHI | Condition |
|------|-----------|
| < 5 | Normal |
| 5–15 | Mild |
| 15–30 | Moderate |
| > 30 | Severe |

---

-> Database Schema

- users
- patients
- sleep_sessions
- sleep_metrics

Designed with normalized relational mapping for efficient report retrieval.

---

-> Deployment

Run locally using Docker:
docker-compose up --build
