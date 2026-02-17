import wfdb
from preprocess import segment_signal

record = wfdb.rdrecord('data/a01')
annotation = wfdb.rdann('data/a01', 'apn')

signal = record.p_signal[:,0]
labels = annotation.symbol

X, y = segment_signal(signal, labels)

print("Total segments:", X.shape)
print("Total labels:", y.shape)
print("First 10 labels:", y[:10])

