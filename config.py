# config.py

# Serial
SERIAL_PORT = 'COM9'
BAUD_RATE    = 115200
WINDOW_SIZE = 200  # Muestras a mostrar en la gráfica 2D
CSV_RAW_FILENAME = "datos_ejercicio_raw.csv"
CSV_FILENAME = "datos_ejercicio.csv"

# Otros parámetros que acabarán siendo configurables
RECORD_LABELS = ["correcto", "error1", "error2", "error3", "error4", "error5"]
DATA_FOLDER   = "./data"
MODEL_PATH    = "./models/modelo_prototipo.joblib"
