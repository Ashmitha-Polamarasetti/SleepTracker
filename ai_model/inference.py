import wfdb
import numpy as np
import wfdb.processing as wp
from tensorflow.keras.models import load_model
from ai_model.preprocess import segment_signal
from ai_model.ahi import calculate_ahi

model = load_model("model.h5")


def calculate_heart_metrics(signal, fs):
    # Detect R peaks
    r_peaks = wp.gqrs_detect(sig=signal, fs=fs)

    # RR intervals in seconds
    rr_intervals = np.diff(r_peaks) / fs

    # Heart Rate (BPM)
    heart_rate = 60 / np.mean(rr_intervals)

    # HRV (SDNN)
    hrv = np.std(rr_intervals)

    return round(float(heart_rate), 2), round(float(hrv), 4)


def simulate_spo2():
    # Simulated realistic SpO2 range
    return round(np.random.uniform(94, 99), 1)


def classify_sleep_stage(heart_rate):
    # Very basic rule-based sleep stage (demo only)
    if heart_rate < 60:
        return "Deep Sleep"
    elif 60 <= heart_rate <= 80:
        return "Light Sleep"
    else:
        return "REM"


def predict_psg(record_name):

    record = wfdb.rdrecord(f"uploaded_files/{record_name}")
    annotation = wfdb.rdann(f"uploaded_files/{record_name}", 'apn')

    signal = record.p_signal[:, 0]
    fs = record.fs
    labels = annotation.symbol

    # ---- AHI pipeline ----
    X, _ = segment_signal(signal, labels)
    X = (X - np.mean(X)) / np.std(X)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    predictions = model.predict(X)
    binary_predictions = (predictions > 0.5).astype(int).flatten()

    ahi, severity, events = calculate_ahi(binary_predictions, len(binary_predictions))

    # ---- Heart Metrics ----
    heart_rate, hrv = calculate_heart_metrics(signal, fs)

    # ---- Simulated Metrics ----
    spo2 = simulate_spo2()
    sleep_stage = classify_sleep_stage(heart_rate)

    return {
        "name": "Demo Patient",
        "email": "demo@hospital.com",
        "session_date": "2026-02-18",
        "heart_rate": heart_rate,
        "hrv": hrv,
        "spo2": spo2,
        "sleep_stage": sleep_stage,
        "ahi": round(float(ahi), 2),
        "severity": severity,
        "total_events": int(events)
    }
