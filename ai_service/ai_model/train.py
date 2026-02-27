import wfdb
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense
from ai_model.preprocess import segment_signal

# Load data
record = wfdb.rdrecord('data/a01')
annotation = wfdb.rdann('data/a01', 'apn')

signal = record.p_signal[:,0]
labels = annotation.symbol

# Segment
X, y = segment_signal(signal, labels)

# Normalize
X = (X - np.mean(X)) / np.std(X)

# Reshape for CNN
X = X.reshape((X.shape[0], X.shape[1], 1))

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Build CNN
model = Sequential([
    Conv1D(32, 5, activation='relu', input_shape=(6000,1)),
    MaxPooling1D(2),
    Conv1D(64, 5, activation='relu'),
    MaxPooling1D(2),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print("Starting training...")

model.fit(X_train, y_train, epochs=5, batch_size=16)

print("Evaluating...")

loss, accuracy = model.evaluate(X_test, y_test)

print("Test Accuracy:", accuracy)

model.save("model.h5")

print("Model saved as model.h5")

