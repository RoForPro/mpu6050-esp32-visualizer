import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph.opengl as gl
import threading
import time
import numpy as np
import csv

# ==========================
# CONFIGURACIÓN
# ==========================
SERIAL_PORT = 'COM9'
BAUD_RATE = 115200
WINDOW_SIZE = 200  # Muestras a mostrar en la gráfica 2D
CSV_FILENAME = "datos_ejercicio_raw.csv"

# Variable para detener de forma segura el hilo de lectura
running = True

# ==========================
# VARIABLES GLOBALES PARA GRÁFICA 2D
# ==========================
data_lock = threading.Lock()
yaw_data = []
pitch_data = []
roll_data = []

# ==========================
# VARIABLES PARA REGISTRO DE REPETICIONES
# ==========================
rep_lock = threading.Lock()
current_repetition_active = False  # Indica si ya se inició una repetición
current_repetition_type = None  # "correcto" o "incorrecto"
current_repetition_data = []  # Almacena [timestamp, yaw, pitch, roll] de la repetición
repetition_count = 0

# Crear archivo CSV con cabecera
with open(CSV_FILENAME, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["rep_id", "timestamp", "yaw", "pitch", "roll", "etiqueta"])


# ==========================
# FUNCIÓN: Guardar la repetición en el CSV
# ==========================
def guardar_repeticion(etiqueta):
    global repetition_count, current_repetition_active, current_repetition_data, current_repetition_type
    with rep_lock:
        if not current_repetition_active or not current_repetition_data:
            print("❗ No hay una repetición activa con datos para guardar.")
            return
        # Verificar que la etiqueta coincide con la de la repetición activa
        if current_repetition_type != etiqueta:
            print("❗ La repetición activa no corresponde a la etiqueta solicitada.")
            return
        repetition_count += 1
        rep_id = repetition_count
        datos_repeticion = current_repetition_data.copy()
        # Resetear la repetición
        current_repetition_active = False
        current_repetition_type = None
        current_repetition_data = []

    # Guardar en CSV (realizado fuera del bloqueo para minimizar bloqueos)
    try:
        with open(CSV_FILENAME, mode='a', newline='') as f:
            writer = csv.writer(f)
            for fila in datos_repeticion:
                writer.writerow([rep_id] + fila + [etiqueta])
        print(f"✅ Repetición {rep_id} guardada ({len(datos_repeticion)} muestras) como '{etiqueta}'.")
    except Exception as e:
        print("Error guardando repetición:", e)


# ==========================
# FUNCIÓN: Lectura de datos desde el ESP32
# ==========================
def getData():
    global yaw_data, pitch_data, roll_data, current_repetition_active, current_repetition_data, running
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Puerto serie abierto:", ser.name)
        time.sleep(2)  # Dar tiempo a estabilizar el ESP32
        # Descartar las primeras 10 líneas (boot)
        for _ in range(10):
            ser.readline()

        # Mensaje de información para el usuario
        print("> IMPORTANTE el foco tienes que estar en la ventana de \"Visualización 2D y registro de repeticiones\" "
              "si no, no funcionarán los comandos de teclado!!!")
        print("Funciones:"
              "\n\t- Pulse \"q\" para iniciar el registro de una repetición CORRECTA."
              "\n\t\t- Pulse \"w\" para finalizar el registro de una repetición CORRECTA."
              "\n\t- Pulse \"e\" para iniciar el registro de una repetición INCORRECTA."
              "\n\t\t- Pulse \"r\" para finalizar el registro de una repetición INCORRECTA."
              "\n\t- Pulse \"x\" para finalizar el registro y salir del programa de forma controlada.")
        while running:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split(',')
                if len(parts) == 4:
                    try:
                        timestamp = float(parts[0])
                        yaw = float(parts[1])
                        pitch = float(parts[2])
                        roll = float(parts[3])

                        # Actualizar listas para la gráfica 2D
                        with data_lock:
                            yaw_data.append(yaw)
                            pitch_data.append(pitch)
                            roll_data.append(roll)
                            if len(yaw_data) > WINDOW_SIZE:
                                yaw_data.pop(0)
                                pitch_data.pop(0)
                                roll_data.pop(0)

                        # Si se está registrando una repetición, almacenar la muestra
                        with rep_lock:
                            if current_repetition_active:
                                current_repetition_data.append([timestamp, yaw, pitch, roll])
                    except ValueError:
                        pass
    except Exception as e:
        print("Error en getData:", e)
    finally:
        if ser and ser.is_open:
            ser.close()
        print("Hilo de lectura finalizado.")


# ==========================
# FUNCIÓN: Crear malla de cubo (reemplaza a gl.MeshData.cube())
# ==========================
def create_cube_mesh():
    # Definir los 8 vértices de un cubo centrado en el origen, tamaño 2
    vertices = np.array([[-1, -1, -1],
                         [1, -1, -1],
                         [1, 1, -1],
                         [-1, 1, -1],
                         [-1, -1, 1],
                         [1, -1, 1],
                         [1, 1, 1],
                         [-1, 1, 1]], dtype=np.float32)
    # Definir las caras (triángulos)
    faces = np.array([[0, 1, 2], [0, 2, 3],  # cara inferior
                      [4, 5, 6], [4, 6, 7],  # cara superior
                      [0, 1, 5], [0, 5, 4],  # cara frontal
                      [2, 3, 7], [2, 7, 6],  # cara trasera
                      [0, 3, 7], [0, 7, 4],  # cara lateral izquierda
                      [1, 2, 6], [1, 6, 5]], dtype=np.int32)
    return gl.MeshData(vertexes=vertices, faces=faces)


# ==========================
# FUNCIÓN: Inicializar y actualizar la vista 3D
# ==========================
def init_3d_view():
    view = gl.GLViewWidget()
    view.setWindowTitle('Visualización 3D IMU')
    view.setCameraPosition(distance=40)
    view.opts['azimuth'] = 45
    view.opts['elevation'] = 30
    view.show()

    # Agregar una cuadrícula para referencia
    grid = gl.GLGridItem()
    grid.setSize(20, 20)
    grid.setSpacing(1, 1)
    view.addItem(grid)

    # Crear un cubo para representar el sensor usando la función auxiliar
    md = create_cube_mesh()  # Genera la malla de un cubo

    sensor_cube = gl.GLMeshItem(meshdata=md, smooth=False, color=(1, 0, 0, 0.8),
                                shader='shaded', drawEdges=True)
    sensor_cube.translate(0, 0, 0)
    view.addItem(sensor_cube)

    return view, sensor_cube


def update_3d():
    # Obtener los valores más recientes para la 3D
    with data_lock:
        if yaw_data:
            latest_yaw = yaw_data[-1]
            latest_pitch = pitch_data[-1]
            latest_roll = roll_data[-1]
        else:
            latest_yaw = latest_pitch = latest_roll = 0
    # Reiniciar la transformación y aplicar rotaciones (orden: yaw, pitch, roll)
    sensor_cube.resetTransform()
    sensor_cube.rotate(latest_yaw, 0, 0, 1)  # Yaw: rotación en torno al eje Z
    sensor_cube.rotate(latest_pitch, 0, 1, 0)  # Pitch: eje Y
    sensor_cube.rotate(latest_roll, 1, 0, 0)  # Roll: eje X


# ==========================
# CONFIGURACIÓN DE LA GRÁFICA 2D
# ==========================
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(title="Visualización 2D y registro de repeticiones")
win.resize(1000, 600)
plot = win.addPlot(title="Yaw, Pitch, Roll (°)")
plot.setLabel('left', "Ángulo (°)")
plot.setLabel('bottom', "Muestras")
plot.setYRange(-90, 90)
plot.setXRange(0, WINDOW_SIZE)
plot.addLegend(offset=(10, 10))

curve_yaw = plot.plot(pen='r', name="Yaw")
curve_pitch = plot.plot(pen='g', name="Pitch")
curve_roll = plot.plot(pen='b', name="Roll")
win.show()


# ==========================
# FUNCIÓN: Actualizar la gráfica 2D en tiempo real
# ==========================
def update_2d():
    with data_lock:
        if yaw_data:
            x = np.arange(len(yaw_data))
            curve_yaw.setData(x, np.array(yaw_data))
            curve_pitch.setData(x, np.array(pitch_data))
            curve_roll.setData(x, np.array(roll_data))
    QtWidgets.QApplication.processEvents()


# Temporizador para 2D
timer_2d = QtCore.QTimer()
timer_2d.timeout.connect(update_2d)
timer_2d.start(50)

# ==========================
# INICIALIZAR VENTANA 3D Y TEMPORIZADOR
# ==========================
view_3d, sensor_cube = init_3d_view()
timer_3d = QtCore.QTimer()
timer_3d.timeout.connect(update_3d)
timer_3d.start(50)


# ==========================
# FUNCIÓN: Salida controlada del programa
# ==========================
def exit_program():
    global running
    print("Finalizando programa de forma controlada...")
    running = False
    app.quit()


# ==========================
# CAPTURA DE TECLADO
# ==========================
def keyPressEvent(event):
    global current_repetition_active, current_repetition_type, current_repetition_data
    tecla = event.text().lower()
    # Iniciar repetición correcta: tecla 'q'
    if tecla == 'q':
        with rep_lock:
            if not current_repetition_active:
                current_repetition_active = True
                current_repetition_type = "correcto"
                current_repetition_data.clear()
                print("▶ Iniciado registro de repetición CORRECTA.")
            else:
                print("❗ Ya hay una repetición activa. Finaliza la actual antes de iniciar otra.")
    # Iniciar repetición incorrecta: tecla 'e'
    elif tecla == 'e':
        with rep_lock:
            if not current_repetition_active:
                current_repetition_active = True
                current_repetition_type = "incorrecto"
                current_repetition_data.clear()
                print("▶ Iniciado registro de repetición INCORRECTA.")
            else:
                print("❗ Ya hay una repetición activa. Finaliza la actual antes de iniciar otra.")
    # Finalizar repetición correcta: tecla 'w'
    elif tecla == 'w':
        guardar_repeticion("correcto")
    # Finalizar repetición incorrecta: tecla 'r'
    elif tecla == 'r':
        guardar_repeticion("incorrecto")
    # Finalizar el programa de forma controlada: tecla 'x'
    elif tecla == 'x':
        exit_program()



# Conectar el manejo de teclas a la ventana principal y a la 3D
win.keyPressEvent = keyPressEvent
view_3d.keyPressEvent = keyPressEvent  # También para la ventana 3D

# ==========================
# INICIAR HILO DE LECTURA DE DATOS
# ==========================
dataThread = threading.Thread(target=getData, daemon=True)
dataThread.start()

# ==========================
# EJECUCIÓN DE LA APLICACIÓN
# ==========================
app.exec_()
print("Programa finalizado correctamente.")
