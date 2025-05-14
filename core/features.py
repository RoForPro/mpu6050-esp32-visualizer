# core/features.py

import numpy as np
from scipy.signal import find_peaks

def extract_features(group):
    """
    Dada la subtabla DataFrame de una repetición (múltiples sensores),
    calcula características estadísticas y dinámicas sobre yaw, pitch, roll.
    """
    feat = {}
    # Normalizamos tiempo en segundos
    t = (group["timestamp"].values - group["timestamp"].values[0])  # en s si ya está en s
    if t.max() > 1e3:  # si está en ms
        t = t / 1000.0

    feat["duration"] = t[-1] - t[0]

    for axis in ("yaw", "pitch", "roll"):
        x = group[axis].values
        feat[f"{axis}_mean"]  = x.mean()
        feat[f"{axis}_std"]   = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()

        # Velocidades
        dx = np.diff(x)
        dt = np.diff(t)
        # evitar división por cero
        vel = np.abs(dx / np.where(dt == 0, 1e-6, dt))
        feat[f"{axis}_vel_mean"] = vel.mean() if len(vel) else 0.0
        feat[f"{axis}_vel_max"]  = vel.max()  if len(vel) else 0.0

        # Picos
        peaks = find_peaks(x)[0]
        feat[f"{axis}_num_peaks"] = len(peaks)

    # Correlaciones
    feat["corr_yaw_pitch"]  = np.corrcoef(group["yaw"],   group["pitch"])[0, 1]
    feat["corr_yaw_roll"]   = np.corrcoef(group["yaw"],   group["roll"])[0, 1]
    feat["corr_pitch_roll"] = np.corrcoef(group["pitch"], group["roll"])[0, 1]

    # Energía combinada
    feat["energy_total"] = (group["yaw"]**2).mean() + \
                           (group["pitch"]**2).mean() + \
                           (group["roll"]**2).mean()

    return feat
