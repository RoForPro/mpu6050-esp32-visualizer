import serial
import threading
import time
import numpy as np
from joblib import load
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from skeleton_renderer import Skeleton3D
from scipy.signal import find_peaks

# ==========================
# CONFIGURACIÓN
# ==========================
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200
WINDOW_SIZE = 200  # Muestras a mostrar en la gráfica 2D

# Carga el pipeline guardado (escalador + modelo)
pipe = load("modelo_prototipo.joblib")

# Control de hilo
running = True

# Datos para visualización 2D
data_lock = threading.Lock()
yaw_data, pitch_data, roll_data = [], [], []

# Para segmentación + predicción
rep_lock = threading.Lock()
current_active = False
current_data = []
rep_count = 0

def extract_feat_list(lst):
    # lst: [[ts,y,p,r],...]
    arr = np.array(lst)
    t = (arr[:,0] - arr[0,0]) / 1000.0
    feat = {"duration": t[-1] - t[0]}
    for i, axis in enumerate(["yaw","pitch","roll"]):
        x = arr[:,1+i]
        feat[f"{axis}_mean"]  = x.mean()
        feat[f"{axis}_std"]   = x.std()
        feat[f"{axis}_range"] = x.max()-x.min()
        dx = np.diff(x); dt = np.diff(t)
        vel = np.abs(dx/dt)
        feat[f"{axis}_vel_mean"] = vel.mean()
        feat[f"{axis}_vel_max"]  = vel.max()
        feat[f"{axis}_num_peaks"] = len(find_peaks(x)[0])
    feat["corr_yaw_pitch"]  = np.corrcoef(arr[:,1], arr[:,2])[0,1]
    feat["corr_yaw_roll"]   = np.corrcoef(arr[:,1], arr[:,3])[0,1]
    feat["corr_pitch_roll"] = np.corrcoef(arr[:,2], arr[:,3])[0,1]
    feat["energy_total"]    = (arr[:,1]**2).mean() + (arr[:,2]**2).mean() + (arr[:,3]**2).mean()
    return feat

# ==========================
# LECTURA DEL PUERTO SERIE
# ==========================
def getData():
    global running
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Puerto serie abierto:", ser.name)
    time.sleep(2)
    for _ in range(10):
        ser.readline()
    # Menú de usuario
    print("\n=== MENÚ PREDICTOR EN VIVO ===")
    print("  q → INICIAR repetición")
    print("  w → FINALIZAR repetición y predecir")
    print("  x → SALIR\n")
    while running:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts)==4:
            ts,y,p,r = map(float, parts)
            with data_lock:
                yaw_data.append(y); pitch_data.append(p); roll_data.append(r)
                if len(yaw_data)>WINDOW_SIZE:
                    yaw_data.pop(0); pitch_data.pop(0); roll_data.pop(0)
            with rep_lock:
                if current_active:
                    current_data.append([ts,y,p,r])
    ser.close()
    print("Hilo de lectura detenido.")

# ==========================
# INICIALIZAR VENTANAS GRÁFICAS
# ==========================
app = QtWidgets.QApplication([])

# Ventana 2D
win2d = pg.GraphicsLayoutWidget(title="Visualización 2D")
win2d.resize(800,500)
plot = win2d.addPlot(title="Yaw, Pitch, Roll (°)")
plot.setLabel('left','Ángulo (°)'); plot.setLabel('bottom','Muestra')
plot.setYRange(-90,90); plot.setXRange(0,WINDOW_SIZE)
plot.addLegend()
c_y = plot.plot(pen='r', name="Yaw")
c_p = plot.plot(pen='g', name="Pitch")
c_r = plot.plot(pen='b', name="Roll")
win2d.show()

# ––– VISTA 3D ESQUELETO –––
skel3d = Skeleton3D()

# Temporizadores
def update_2d():
    with data_lock:
        if yaw_data:
            x = np.arange(len(yaw_data))
            c_y.setData(x, np.array(yaw_data))
            c_p.setData(x, np.array(pitch_data))
            c_r.setData(x, np.array(roll_data))
    QtWidgets.QApplication.processEvents()

timer2 = QtCore.QTimer()
timer2.timeout.connect(update_2d)
timer2.start(50)

timer3 = QtCore.QTimer()
timer3.timeout.connect(lambda: skel3d.update(
    yaw_data[-1] if yaw_data else 0,
    pitch_data[-1] if pitch_data else 0,
    roll_data[-1] if roll_data else 0))
timer3.start(50)

# ==========================
# PREDICCIÓN Y SEGMENTACIÓN
# ==========================
def finalize_rep():
    global rep_count, current_active, current_data
    with rep_lock:
        if not current_active:
            return
        rep_count += 1
        data = current_data.copy()
        current_data.clear()
        current_active = False
    feat = extract_feat_list(data)
    import pandas as _pd
    df_feat = _pd.DataFrame([feat])
    y_pred = pipe.predict(df_feat)[0]
    prob   = pipe.predict_proba(df_feat)[0][y_pred]
    label  = "CORRECTO" if y_pred==1 else "INCORRECTO"
    print(f"\n▶ Repetición {rep_count} → {label} (p={prob:.2f})\n")

def keyPressEvent(ev):
    global current_active
    k = ev.text().lower()
    if k=='q' and not current_active:
        current_active = True
        current_data.clear()
        print("▶ Inicio de repetición")
    elif k=='w' and current_active:
        finalize_rep()
    elif k=='x':
        print("Saliendo…")
        global running
        running = False
        app.quit()

win2d.keyPressEvent = keyPressEvent
skel3d.keyPressEvent = keyPressEvent

# ==========================
# ARRANQUE
# ==========================
threading.Thread(target=getData, daemon=True).start()
app.exec_()
print("Programa finalizado correctamente.")
