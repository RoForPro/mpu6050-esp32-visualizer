# test_acquisition.py

import time
import os
import config
from core.acquisition import CaptureController

def ensure_data_folder():
    os.makedirs(config.DATA_FOLDER, exist_ok=True)

def main():
    ensure_data_folder()
    raw_path   = os.path.join(config.DATA_FOLDER, config.CSV_RAW_FILENAME)
    label_path = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)

    ctrl = CaptureController(
        sensor_configs=config.SENSORS,
        raw_filepath=raw_path,
        labeled_filepath=label_path
    )

    print("→ Arrancando captura raw durante 2 segundos...")
    ctrl.start_recording()
    time.sleep(2)

    print("→ Iniciando segmento etiqueta 'correcto' (3s)...")
    ctrl.start_segment("correcto")
    time.sleep(3)
    ctrl.stop_segment()
    print("→ Segmento 'correcto' finalizado.")

    print("→ Iniciando segmento etiqueta 'incorrecto' (2s)...")
    ctrl.start_segment("incorrecto")
    time.sleep(2)
    ctrl.stop_segment()
    print("→ Segmento 'incorrecto' finalizado.")

    time.sleep(1)
    print("→ Parando grabación.")
    ctrl.stop_recording()

    print(f"Comprueba ahora los ficheros:\n - RAW:  {raw_path}\n - LABELED: {label_path}")

if __name__ == "__main__":
    main()
