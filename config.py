# config.py

# Serial
SERIAL_PORT      = 'COM9'
BAUD_RATE        = 115200
WINDOW_SIZE      = 200  # Muestras a mostrar en la gráfica 2D
CSV_RAW_FILENAME = "datos_ejercicio_raw.csv"
CSV_FILENAME     = "datos_ejercicio.csv"

# Etiquetas posibles durante el registro
RECORD_LABELS    = ["correcto", "incorrecto"]  # más tarde: ["error1", "error2", ...]

# Carpeta de datos y modelo
DATA_FOLDER      = "./data"
MODEL_PATH       = "./models/modelo_prototipo.joblib"

# Configuración de sensores IMU
# Cada entry se pasará a SensorManager
SENSORS = [
    {"id": "imu1", "port": SERIAL_PORT, "baud_rate": BAUD_RATE},
    # Ejemplo para futuro:
    # {"id": "imu2", "port": "COM10", "baud_rate": BAUD_RATE},
    # {"id": "imu3", "port": "COM11", "baud_rate": BAUD_RATE},
]
