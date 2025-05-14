# ui/widgets/offline_widget.py

import os
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import config

class OfflineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Indicador de si los datos ya se han cargado
        self._data_loaded = False
        self._reps = []
        self._idx = 0

        # — 1) Creamos la UI base sin datos—
        self._lbl_title = QLabel("Visualización Offline")
        self._lbl_title.setAlignment(Qt.AlignCenter)

        self._plot = pg.PlotWidget(title="Yaw / Pitch / Roll")
        self._plot.addLegend()
        self._plot.setLabel('left', 'Ángulo (°)')
        self._plot.setLabel('bottom', 'Tiempo (s)')
        self._curves = {
            'yaw':   self._plot.plot(pen='r', name='Yaw'),
            'pitch': self._plot.plot(pen='g', name='Pitch'),
            'roll':  self._plot.plot(pen='b', name='Roll'),
        }

        self.btn_prev = QPushButton("Anterior")
        self.btn_next = QPushButton("Siguiente")
        self.btn_prev.clicked.connect(self.prev)
        self.btn_next.clicked.connect(self.next)
        # Deshabilitamos la navegación hasta cargar datos
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self._lbl_title)
        layout.addWidget(self._plot, stretch=1)
        layout.addLayout(nav_layout)

    def showEvent(self, event):
        """
        Llamado cuando el widget se muestra por primera vez.
        Aquí cargamos los datos solo una vez.
        """
        super().showEvent(event)
        if not self._data_loaded:
            self.load_data()

    def load_data(self):
        """
        Carga y valida el CSV, agrupa por rep_id y despliega la primera repetición.
        Muestra errores con QMessageBox en caso de fallo.
        """
        csv_path = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)
        if not os.path.exists(csv_path):
            QMessageBox.critical(self, "Error", f"No se encuentra el archivo CSV:\n{csv_path}")
            return

        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                QMessageBox.warning(self, "Advertencia", "El archivo CSV está vacío")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el CSV:\n{e}")
            return

        # Aceptar 'etiqueta' o 'label'
        if 'etiqueta' in df.columns and 'label' not in df.columns:
            df = df.rename(columns={'etiqueta': 'label'})

        required = {'rep_id', 'timestamp', 'yaw', 'pitch', 'roll', 'label'}
        miss = required - set(df.columns)
        if miss:
            QMessageBox.critical(self, "Error", f"Faltan columnas en CSV:\n{miss}")
            return

        # Agrupamos por rep_id
        grouped = df.groupby('rep_id')
        self._reps = [(rid, grp) for rid, grp in grouped]
        if not self._reps:
            QMessageBox.information(self, "Info", "No hay repeticiones en el CSV")
            return

        # Datos listos: activamos navegación y pintamos la primera
        self._data_loaded = True
        self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(True)
        self._idx = 0
        self._update_plot()

    def _update_plot(self):
        """
        Dibuja en la gráfica la repetición self._idx de self._reps.
        """
        rep_id, grp = self._reps[self._idx]
        label = grp['label'].iloc[0]
        t0 = grp['timestamp'].iloc[0]
        tiempo = grp['timestamp'] - t0

        self._lbl_title.setText(f"Repetición {rep_id} — {label}")

        for key, curve in self._curves.items():
            curve.setData(tiempo.values, grp[key].values)

    def prev(self):
        """Navegar a la repetición anterior."""
        if not self._data_loaded:
            return
        self._idx = (self._idx - 1) % len(self._reps)
        self._update_plot()

    def next(self):
        """Navegar a la repetición siguiente."""
        if not self._data_loaded:
            return
        self._idx = (self._idx + 1) % len(self._reps)
        self._update_plot()
