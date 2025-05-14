# core/predictor.py

import threading
import pandas as pd
import time
from joblib import load
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

from core.features import extract_features
from core.imu.manager import SensorManager
import config

class PredictorController(QObject):
    """
    Controlador para predicción en vivo:
    - Lee IMUs sólo tras start()
    - Segmenta repeticiones y lanza predicción
    """
    data_ready        = pyqtSignal(dict)          # cada lectura {'sensor_id',...}
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    segment_started   = pyqtSignal()
    segment_stopped   = pyqtSignal()
    prediction_ready  = pyqtSignal(str, float)    # (label, probabilidad)

    def __init__(self, sensor_configs, model_path):
        super().__init__()
        # Sólo guardamos configs; NO abrimos nada aún
        self.sensor_configs = sensor_configs
        self.sm             = None
        self.model          = load(model_path)

        self._thread     = None
        self._stop_event = threading.Event()

        self._seg_active = False
        self._buffer     = []

    def start(self):
        """Arranca la lectura continua (y abre los sensores en este momento)."""
        # 1) Si aún no hay SensorManager, lo creamos ahora
        if self.sm is None:
            self.sm = SensorManager(self.sensor_configs)

        # 2) Si el hilo ya corre, no hacemos nada
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.recording_started.emit()

    def stop(self):
        """Para la lectura y cierra los sensores."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        if self.sm:
            self.sm.close_all()
            self.sm = None
        self.recording_stopped.emit()

    def start_segment(self):
        """Marca el inicio de una repetición."""
        if not self._seg_active:
            self._seg_active = True
            self._buffer = []
            self.segment_started.emit()

    def stop_segment(self):
        """Marca el fin de la repetición y emite la predicción."""
        if not self._seg_active:
            return
        self._seg_active = False
        self.segment_stopped.emit()

        # 1) Convertir buffer a DataFrame ordenado y extraer features
        # Ordena por timestamp y lo convierte en DataFrame
        df_rep = pd.DataFrame(sorted(self._buffer, key=lambda d: d['timestamp']))
        feat = extract_features(df_rep)
        df_feat = pd.DataFrame([feat])

        # 2) Predecir con el modelo
        y_pred = self.model.predict(df_feat)[0]
        proba  = self.model.predict_proba(df_feat)[0][
            list(self.model.classes_).index(y_pred)
        ]

        # 3) Mapear a nombre legible (opcionalmente en config)
        label = getattr(config, "LABEL_NAME_MAP", {}).get(y_pred, str(y_pred))
        self.prediction_ready.emit(label, float(proba))

    def _loop(self):
        """Bucle que lee datos y emite señales."""
        while not self._stop_event.is_set():
            readings = self.sm.read_all()
            for rd in readings:
                self.data_ready.emit(rd)
                if self._seg_active:
                    self._buffer.append(rd)
            time.sleep(0.001)
