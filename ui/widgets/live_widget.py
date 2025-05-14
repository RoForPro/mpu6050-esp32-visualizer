# ui/widgets/live_widget.py

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QShortcut
)

import config
from core.predictor import PredictorController
from visualization.plot2d import Plot2DWidget


class LiveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # — Controles principales—
        self.btn_start = QPushButton("Iniciar")
        self.btn_stop = QPushButton("Detener")
        self.btn_start_segment = QPushButton("Iniciar Reconocimiento")
        self.btn_stop_segment = QPushButton("Detener Repetición")
        self.status_label = QLabel("Estado: Detenido")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Configuramos estados iniciales
        self.btn_stop.setEnabled(False)
        self.btn_start_segment.setEnabled(False)
        self.btn_stop_segment.setEnabled(False)

        # Layout de controles
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        ctrl_layout.addWidget(self.btn_start_segment)
        ctrl_layout.addWidget(self.btn_stop_segment)
        ctrl_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        ctrl_layout.addWidget(self.status_label)

        # — Plots 2D por sensor—
        self.plot_layout = QHBoxLayout()
        self.plot2d_widgets = {}
        for cfg in config.SENSORS:
            sid = cfg['id']
            pw = Plot2DWidget(sensor_id=sid, window_size=config.WINDOW_SIZE)
            self.plot2d_widgets[sid] = pw
            self.plot_layout.addWidget(pw, stretch=1)

        # Montaje principal
        main = QVBoxLayout(self)
        main.addLayout(ctrl_layout)
        main.addLayout(self.plot_layout)

        # — Controller de predicción—
        self.ctrl = PredictorController(
            sensor_configs=config.SENSORS,
            model_path=os.path.join(config.MODEL_PATH)
        )

        # Conexiones UI → Controller
        self.btn_start.clicked.connect(self.ctrl.start)
        self.btn_stop.clicked.connect(self.ctrl.stop)
        self.btn_start_segment.clicked.connect(self.ctrl.start_segment)
        self.btn_stop_segment.clicked.connect(self.ctrl.stop_segment)

        # — Atajos de teclado —
        # Espacio = Alternar entre Iniciar/Detener repetición
        self._recording_segment = False  # Variable para controlar el estado
        sc_toggle = QShortcut(QKeySequence("Space"), self)
        sc_toggle.activated.connect(self._toggle_segment)

        # Conexiones Controller → UI
        self.ctrl.data_ready.connect(self._on_data_ready)
        self.ctrl.recording_started.connect(self._on_recording_started)
        self.ctrl.recording_stopped.connect(self._on_recording_stopped)
        self.ctrl.segment_started.connect(self._on_segment_started)
        self.ctrl.segment_stopped.connect(self._on_segment_stopped)
        self.ctrl.prediction_ready.connect(self._on_prediction_ready)

    def _toggle_segment(self):
        """Alterna entre iniciar y detener la repetición"""
        if not self._recording_segment and self.btn_start_segment.isEnabled():
            self.ctrl.start_segment()
            self._recording_segment = True
        elif self._recording_segment and self.btn_stop_segment.isEnabled():
            self.ctrl.stop_segment()
            self._recording_segment = False

    def _on_data_ready(self, reading: dict):
        sid = reading.get('sensor_id')
        if sid in self.plot2d_widgets:
            self.plot2d_widgets[sid].update_data(reading)

    def _on_recording_started(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_start_segment.setEnabled(True)
        self.status_label.setText("Estado: Activo")
        self.status_label.setStyleSheet("color: blue;")

    def _on_recording_stopped(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_start_segment.setEnabled(False)
        self.btn_stop_segment.setEnabled(False)
        self.status_label.setText("Estado: Detenido")
        self.status_label.setStyleSheet("color: black;")

    def _on_segment_started(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_start_segment.setEnabled(False)
        self.btn_stop_segment.setEnabled(True)
        self.status_label.setText("Estado: Analizando repetición...")
        self.status_label.setStyleSheet("color: green;")

    def _on_segment_stopped(self):
        self.btn_stop_segment.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_start_segment.setEnabled(True)
        self.status_label.setText("Estado: Procesando predicción…")
        self.status_label.setStyleSheet("color: orange;")

    def _on_prediction_ready(self, label: str, proba: float):
        # Mostrar resultado con probabilidad
        text = f"{label} — {proba * 100:.1f}%"
        self.status_label.setText(text)
        self.status_label.setStyleSheet("background: lightgray;")
