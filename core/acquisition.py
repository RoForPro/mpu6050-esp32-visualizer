# core/acquisition.py

import os
import csv
import threading
import time
from typing import List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from core.imu.manager import SensorManager

class DataRecorder:
    """
    Graba datos raw de N IMUs y, cuando se solicita, segmenta
    repeticiones etiquetadas en un CSV aparte.
    """
    def __init__(
        self,
        sensor_manager: SensorManager,
        raw_filepath: str,
        labeled_filepath: str
    ):
        self.sm = sensor_manager
        self.raw_filepath = raw_filepath
        self.labeled_filepath = labeled_filepath
        # Contador de repeticiones
        self._next_rep_id = 1
        self.current_rep_id = None  # TODO Se podría establecer desde la interfaz

        # Aseguramos carpeta destino
        os.makedirs(os.path.dirname(raw_filepath) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(labeled_filepath) or ".", exist_ok=True)

        # Abrimos CSV raw en modo append
        self.raw_file = open(raw_filepath, 'a', newline='')
        self.raw_writer = csv.writer(self.raw_file)
        # Escribimos cabecera si está vacío
        if os.stat(raw_filepath).st_size == 0:
            self.raw_writer.writerow(['timestamp', 'sensor_id', 'yaw', 'pitch', 'roll'])

        # Abrimos CSV labeled en modo append
        self.labeled_file = open(labeled_filepath, 'a', newline='')
        self.labeled_writer = csv.writer(self.labeled_file)
        if os.stat(labeled_filepath).st_size == 0:
            self.labeled_writer.writerow(
                ['rep_id', 'timestamp', 'sensor_id', 'yaw', 'pitch', 'roll', 'label']
            )

        # Estado de segmento
        self.segment_active = False
        self.current_label = None
        self.current_buffer: List[Dict[str, Any]] = []

    def start_segment(self, label: str):
        """Inicia una repetición etiquetada con `label`."""
        if not self.segment_active:
            self.segment_active = True
            self.current_label = label
            self.current_rep_id = self._next_rep_id
            self._next_rep_id += 1
            self.current_buffer = []

    def stop_segment(self):
        """Finaliza la repetición, vuelca el buffer al CSV de etiquetas."""
        if not self.segment_active:
            return
        for reading in self.current_buffer:
            self.labeled_writer.writerow([
                self.current_rep_id,
                reading['timestamp'],
                reading['sensor_id'],
                reading['yaw'],
                reading['pitch'],
                reading['roll'],
                self.current_label
            ])
        self.labeled_file.flush()
        self.segment_active = False
        self.current_label = None
        self.current_buffer = []

    def write_raw(self, reading: Dict[str, Any]):
        """Escribe una medida raw en el CSV correspondiente."""
        self.raw_writer.writerow([
            reading['timestamp'],
            reading['sensor_id'],
            reading['yaw'],
            reading['pitch'],
            reading['roll']
        ])
        self.raw_file.flush()

    def close(self):
        """Cierra los ficheros."""
        self.raw_file.close()
        self.labeled_file.close()


class CaptureController(QObject):
    """
    Controller que lanza el bucle de adquisición en un hilo,
    delega en DataRecorder y emite señales Qt para la UI.
    """
    # Señal por cada nueva lectura (un dict con keys: timestamp, sensor_id, yaw, pitch, roll)
    data_ready = pyqtSignal(dict)
    # Señal al iniciar/parar segmento (label o vacía)
    segment_started = pyqtSignal(str)
    segment_stopped = pyqtSignal()

    def __init__(
        self,
        sensor_configs: List[Dict[str, Any]],
        raw_filepath: str,
        labeled_filepath: str
    ):
        super().__init__()
        self.recorder = DataRecorder(
            sensor_manager=SensorManager(sensor_configs),
            raw_filepath=raw_filepath,
            labeled_filepath=labeled_filepath
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread = None

    def start_recording(self):
        """Arranca el hilo que lee continuamente de las IMUs."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop_recording(self):
        """Pide parada al hilo, espera a que termine y cierra sensores y ficheros."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.recorder.sm.close_all()
        self.recorder.close()

    def start_segment(self, label: str):
        """Señala al recorder que empiece a acumular datos con esta etiqueta."""
        self.recorder.start_segment(label)
        self.segment_started.emit(label)

    def stop_segment(self):
        """Pide al recorder que acabe la repetición y emita señal."""
        self.recorder.stop_segment()
        self.segment_stopped.emit()

    def _record_loop(self):
        """Bucle interno que lee, escribe y emite cada medida."""
        while not self._stop_event.is_set():
            readings = self.recorder.sm.read_all()
            for reading in readings:
                # 1) graba raw
                self.recorder.write_raw(reading)
                # 2) si hay segmento abierto, acumula
                if self.recorder.segment_active:
                    self.recorder.current_buffer.append(reading)
                # 3) emite señal para UI
                self.data_ready.emit(reading)
            # muy corta pausa para evitar busy‐wait excesivo
            time.sleep(0.001)
