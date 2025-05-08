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

# Mapear las clases numéricas a nombres legibles
#  Aquí invertimos el mapping que usaste en entrenamiento:
label_name_map = {
    0: "INCORRECTO",
    1: "CORRECTO",
    # Si añades más clases en el futuro, extiende este dict:
    # 2: "RECORTE",
    # 3: "REBOTE",
}

palette = [
    "rgba(150,0,0,200)",  # rojo
    "rgba(0,150,0,200)",  # verde
    "rgba(150,150,0,200)",  # amarillo
    "rgba(0,150,150,200)",  # cian
    "rgba(150,0,150,200)",  # magenta
    # …añade más si crees necesarias…
]
# classes = pipe.named_steps['clf'].classes_
# pipeline sólo tiene el escalador y el clasificador
classes = pipe.classes_
label_color_map = {cls: palette[i % len(palette)] for i, cls in enumerate(classes)}

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


# ==========================
# Extracción de características
# ==========================
def extract_feat_list(lst):
    arr = np.array(lst)
    t = (arr[:, 0] - arr[0, 0]) / 1000.0
    feat = {"duration": t[-1] - t[0]}
    for i, axis in enumerate(["yaw", "pitch", "roll"]):
        x = arr[:, 1 + i]
        feat[f"{axis}_mean"] = x.mean()
        feat[f"{axis}_std"] = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()
        dx = np.diff(x);
        dt = np.diff(t)
        vel = np.abs(dx / dt)
        feat[f"{axis}_vel_mean"] = vel.mean()
        feat[f"{axis}_vel_max"] = vel.max()
        feat[f"{axis}_num_peaks"] = len(find_peaks(x)[0])
    feat["corr_yaw_pitch"] = np.corrcoef(arr[:, 1], arr[:, 2])[0, 1]
    feat["corr_yaw_roll"] = np.corrcoef(arr[:, 1], arr[:, 3])[0, 1]
    feat["corr_pitch_roll"] = np.corrcoef(arr[:, 2], arr[:, 3])[0, 1]
    feat["energy_total"] = (arr[:, 1] ** 2).mean() + (arr[:, 2] ** 2).mean() + (arr[:, 3] ** 2).mean()
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
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            # Dividir por comas y limpiar cada parte
            parts = [p.split('\r')[0].strip() for p in line.split(',')]
            if len(parts) == 4:
                # Intentar convertir cada parte a float
                try:
                    ts, y, p, r = [float(p) for p in parts]
                    with data_lock:
                        yaw_data.append(y)
                        pitch_data.append(p)
                        roll_data.append(r)
                        if len(yaw_data) > WINDOW_SIZE:
                            yaw_data.pop(0)
                            pitch_data.pop(0)
                            roll_data.pop(0)
                    with rep_lock:
                        if current_active:
                            current_data.append([ts, y, p, r])
                except ValueError:
                    print("Error al convertir valores:", parts)
                    continue
        except Exception as e:
            print(f"Error en la lectura del puerto serie: {e}")
            continue
    ser.close()
    print("Hilo de lectura detenido.")


# ==========================
# INICIALIZAR VENTANAS GRÁFICAS
# ==========================
app = QtWidgets.QApplication([])

# Ventana 2D
win2d = pg.GraphicsLayoutWidget(title="Visualización 2D")
win2d.resize(800, 500)
plot = win2d.addPlot(title="Yaw, Pitch, Roll (°)")
plot.setLabel('left', 'Ángulo (°)');
plot.setLabel('bottom', 'Muestra')
plot.setYRange(-90, 90);
plot.setXRange(0, WINDOW_SIZE)
plot.addLegend()
c_y = plot.plot(pen='r', name="Yaw")
c_p = plot.plot(pen='g', name="Pitch")
c_r = plot.plot(pen='b', name="Roll")
win2d.show()

# QLabel flotante para predicción
label_pred = QtWidgets.QLabel("", parent=win2d)
label_pred.setStyleSheet("""
    background-color: rgba(50,50,50,200);
    color: white;
    font-size: 16pt;
    border-radius: 8px;
    padding: 5px;
""")
label_pred.setAlignment(QtCore.Qt.AlignCenter)
label_pred.setFixedSize(200, 60)
label_pred.move(10, 10)
label_pred.show()

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
    df_feat = __import__('pandas').DataFrame([feat])
    y_pred = pipe.predict(df_feat)[0]
    prob = pipe.predict_proba(df_feat)[0][list(pipe.classes_).index(y_pred)]
    # Traducir la predicción numérica a texto
    label_text = label_name_map.get(y_pred, str(y_pred)).upper()

    # Color según la clase
    color = label_color_map.get(y_pred, "rgba(80,80,80,200)")

    # Actualizar el QLabel
    label_pred.setStyleSheet(f"""
        background-color: {color};
        color: white;
        font-size: 16pt;
        border-radius: 8px;
        padding: 5px;
    """)
    label_pred.setText(f"{label_text}\nProb: {prob:.2f}")

    print(f"\n▶ Repetición {rep_count} → {label_text} (p={prob:.2f})\n")


def keyPressEvent(ev):
    global current_active
    k = ev.text().lower()
    if k == 'q' and not current_active:
        current_active = True
        current_data.clear()
        print("▶ Inicio de repetición")
    elif k == 'w' and current_active:
        finalize_rep()
    elif k == 'x':
        print("Saliendo…")
        global running
        running = False
        app.quit()


win2d.keyPressEvent = keyPressEvent
skel3d.view.keyPressEvent = keyPressEvent

# ==========================
# ARRANQUE
# ==========================
threading.Thread(target=getData, daemon=True).start()
app.exec_()
print("Programa finalizado correctamente.")
