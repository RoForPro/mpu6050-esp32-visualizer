# scripts/features.py

import numpy as np
from scipy.signal import find_peaks

def extract_from_list(samples):
    """
    Dada una lista de [timestamp, yaw, pitch, roll],
    devuelve un dict con las 17 características.
    """
    arr = np.array(samples)
    t = (arr[:,0] - arr[0,0]) / 1000.0
    feat = {"duration": t[-1] - t[0]}
    for i, axis in enumerate(["yaw","pitch","roll"]):
        x = arr[:,1+i]
        # Básicas
        feat[f"{axis}_mean"]  = x.mean()
        feat[f"{axis}_std"]   = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()
        # Dinámicas
        dx = np.diff(x); dt = np.diff(t)
        vel = np.abs(dx/dt)
        feat[f"{axis}_vel_mean"] = vel.mean()
        feat[f"{axis}_vel_max"]  = vel.max()
        # Picos
        feat[f"{axis}_num_peaks"] = len(find_peaks(x)[0])
    # Correlaciones
    feat["corr_yaw_pitch"]  = np.corrcoef(arr[:,1], arr[:,2])[0,1]
    feat["corr_yaw_roll"]   = np.corrcoef(arr[:,1], arr[:,3])[0,1]
    feat["corr_pitch_roll"] = np.corrcoef(arr[:,2], arr[:,3])[0,1]
    # Energía total
    feat["energy_total"] = (arr[:,1]**2).mean() + (arr[:,2]**2).mean() + (arr[:,3]**2).mean()
    return feat
# scripts/features.py

import numpy as np
from scipy.signal import find_peaks

def extract_from_list(samples):
    """
    Dada una lista de [timestamp, yaw, pitch, roll],
    devuelve un dict con las 17 características.
    """
    arr = np.array(samples)
    t = (arr[:,0] - arr[0,0]) / 1000.0
    feat = {"duration": t[-1] - t[0]}
    for i, axis in enumerate(["yaw","pitch","roll"]):
        x = arr[:,1+i]
        # Básicas
        feat[f"{axis}_mean"]  = x.mean()
        feat[f"{axis}_std"]   = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()
        # Dinámicas
        dx = np.diff(x); dt = np.diff(t)
        vel = np.abs(dx/dt)
        feat[f"{axis}_vel_mean"] = vel.mean()
        feat[f"{axis}_vel_max"]  = vel.max()
        # Picos
        feat[f"{axis}_num_peaks"] = len(find_peaks(x)[0])
    # Correlaciones
    feat["corr_yaw_pitch"]  = np.corrcoef(arr[:,1], arr[:,2])[0,1]
    feat["corr_yaw_roll"]   = np.corrcoef(arr[:,1], arr[:,3])[0,1]
    feat["corr_pitch_roll"] = np.corrcoef(arr[:,2], arr[:,3])[0,1]
    # Energía total
    feat["energy_total"] = (arr[:,1]**2).mean() + (arr[:,2]**2).mean() + (arr[:,3]**2).mean()
    return feat
