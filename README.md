-> Sleep Apnea Detection System

A Full-Stack AI-based healthcare monitoring system for automated sleep apnea detection using ECG signals.

---

-> Project Overview

This system automates sleep apnea detection using a deep learning model trained on the PhysioNet Apnea-ECG dataset. 

Doctors upload PSG files (.dat, .hea, .apn), and the AI service computes clinical metrics such as:

- Heart Rate (HR)
- Heart Rate Variability (HRV)
- Apnea-Hypopnea Index (AHI)
- Severity Classification
- Sleep Stage

Results are stored in PostgreSQL and displayed through role-based dashboards.

---

-> System Architecture

Doctor → Backend (FastAPI) → AI Service (TensorFlow) → PostgreSQL → Dashboard

Services are containerized using Docker Compose:

- sleep_backend
- sleep_ai
- sleep_db

---

-> AI Model

- 1D CNN (TensorFlow)
- Trained on PhysioNet Apnea-ECG dataset
- ~93% accuracy
- Computes AHI and severity classification

---

-> Database Schema

- users
- patients
- sleep_sessions
- sleep_metrics
