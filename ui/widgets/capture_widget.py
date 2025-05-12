# ui/widgets/capture_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel,
    QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

import config
from core.acquisition import CaptureController
from visualization.plot2d import Plot2DWidget
# from visualization.heatmap import HeatmapWidget
# from visualization.renderer3d import Renderer3DWidget

class CaptureWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Rutas de fichero
        raw_path   = os.path.join(config.DATA_FOLDER, config.CSV_RAW_FILENAME)
        label_path = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)

        # Controlador de captura
        self.ctrl = CaptureController(
            sensor_configs=config.SENSORS,
            raw_filepath=raw_path,
            labeled_filepath=label_path
        )

        # — Controles principales—
        self.btn_start = QPushButton("Iniciar Grabación")
        self.btn_stop  = QPushButton("Detener Grabación")

        self.label_combo = QComboBox()
        self.label_combo.addItems(config.RECORD_LABELS)

        self.btn_start_segment = QPushButton("Iniciar Repetición")
        self.btn_stop_segment  = QPushButton("Detener Repetición")

        self.status_label = QLabel("Estado: Detenido")
        self.status_label.setAlignment(Qt.AlignCenter)

        # — Sub-widgets de visualización—
        # Asumen métodos `update_data(reading: dict)`

        # Layout donde irán los plots
        self.plot_layout = QHBoxLayout()

        # Diccionario sensor_id → Plot2DWidget
        self.plot2d_widgets = {}
        for cfg in config.SENSORS:
            sid = cfg['id']
            pw = Plot2DWidget(sensor_id=sid, window_size=config.WINDOW_SIZE)
            self.plot2d_widgets[sid] = pw
            self.plot_layout.addWidget(pw, stretch=1)

        # self.heatmap    = HeatmapWidget()
        # self.renderer3d = Renderer3DWidget()

        # — Layout de controles—
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        ctrl_layout.addWidget(QLabel("Etiqueta:"))
        ctrl_layout.addWidget(self.label_combo)
        ctrl_layout.addWidget(self.btn_start_segment)
        ctrl_layout.addWidget(self.btn_stop_segment)
        ctrl_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        ctrl_layout.addWidget(self.status_label)

        # — Layout principal—
        main_layout = QVBoxLayout()
        main_layout.addLayout(ctrl_layout)

        # — Layout de sub-widgets (2D, heatmap, 3D)—
        # todo sub_layout = QHBoxLayout()
        # sub_layout.addWidget(self.heatmap,    stretch=1)
        # sub_layout.addWidget(self.renderer3d, stretch=2)
        # main_layout.addLayout(sub_layout)
        main_layout.addLayout(self.plot_layout)

        self.setLayout(main_layout)

        # — Conexiones UI → Controller—
        self.btn_start.clicked.connect(self.ctrl.start_recording)
        self.btn_stop.clicked.connect(self.ctrl.stop_recording)
        self.btn_start_segment.clicked.connect(self._on_start_segment)
        self.btn_stop_segment.clicked.connect(self.ctrl.stop_segment)

        # — Conexiones Controller → UI—
        self.ctrl.data_ready.connect(self._on_data_ready)
        self.ctrl.segment_started.connect(self._on_segment_started)
        self.ctrl.segment_stopped.connect(self._on_segment_stopped)

    def _on_start_segment(self):
        label = self.label_combo.currentText()
        self.ctrl.start_segment(label)

    def _on_data_ready(self, reading: dict):
        """
        Lectura recibida:
        - reading = {'sensor_id','timestamp','yaw','pitch','roll','rep_id'?}
        """
        sid = reading.get('sensor_id')
        # Si tenemos un widget para ese IMU, actualízalo
        if sid in self.plot2d_widgets:
            self.plot2d_widgets[sid].update_data(reading)

        # TODO Heatmap y 3D los puedes mantener igual (recibirán
        # todos los readings y filtrar internamente o agregarlos)
        # self.heatmap.update_data(reading)
        # self.renderer3d.update_data(reading)

    def _on_segment_started(self, label: str):
        self.status_label.setText(f"Estado: Grabando (‘{label}’)")
        self.status_label.setStyleSheet("color: green;")

    def _on_segment_stopped(self):
        self.status_label.setText("Estado: Detenido")
        self.status_label.setStyleSheet("color: black;")
