import wfdb
import numpy as np
from tensorflow.keras.models import load_model
from ai_model.preprocess import segment_signal
from ai_model.ahi import calculate_ahi

model = load_model("model.h5")

def predict_psg(record_name):

    record = wfdb.rdrecord(f"uploaded_files/{record_name}")
    annotation = wfdb.rdann(f"uploaded_files/{record_name}", 'apn')

    signal = record.p_signal[:, 0]
    labels = annotation.symbol

    X, _ = segment_signal(signal, labels)

    X = (X - np.mean(X)) / np.std(X)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    predictions = model.predict(X)
    binary_predictions = (predictions > 0.5).astype(int).flatten()

    ahi, severity, events = calculate_ahi(binary_predictions, len(binary_predictions))

    return {
        "ahi": round(float(ahi), 2),
        "severity": severity,
        "total_events": int(events),
        "total_minutes": int(len(binary_predictions))
    }

