import numpy as np

def segment_signal(signal, labels, window_size=6000):
    segments = []
    y = []

    for i in range(len(labels)):
        start = i * window_size
        end = start + window_size

        segment = signal[start:end]

        if len(segment) == window_size:
            segments.append(segment)
            y.append(1 if labels[i] == 'A' else 0)

    return np.array(segments), np.array(y)

