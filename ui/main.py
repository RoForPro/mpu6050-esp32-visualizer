# ui/main.py

import os
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QAction, QWidget, QLabel, QVBoxLayout
)
from PyQt5.QtCore import Qt

import config
from ui.widgets.capture_widget import CaptureWidget
from visualization.plot2d import Plot2DWidget
# Más adelante, cuando los implementes:
# from ui.widgets.training_widget import TrainingWidget
# from ui.widgets.offline_widget  import OfflineWidget
# from ui.widgets.live_widget     import LiveWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Biomecánico v4.0")
        self.resize(1200, 800)

        # Mapa modo → función fábrica que devuelve List[QDockWidget]
        self.mode_map = {
            "capture": [self._make_capture_dock()],
            "training": [self._make_training_dock()],
            "offline": [self._make_offline_dock()],
            "live": [self._make_live_dock()]
        }
        # Lista de docks activos
        self.current_docks = []

        self._setup_menu()
        # Arrancamos en modo captura por defecto
        self.load_mode("capture")

    def _setup_menu(self):
        menu = self.menuBar().addMenu("Modo")

        # Acción Captura y Segmentación
        act_cap = QAction("Captura y Segmentación", self)
        act_cap.triggered.connect(lambda: self.load_mode("capture"))
        menu.addAction(act_cap)

        # Acción Entrenamiento
        act_tr  = QAction("Entrenamiento", self)
        act_tr.triggered.connect(lambda: self.load_mode("training"))
        menu.addAction(act_tr)

        # Acción Visualización Offline
        act_off = QAction("Visualización Offline", self)
        act_off.triggered.connect(lambda: self.load_mode("offline"))
        menu.addAction(act_off)

        # Acción Predicción en Vivo
        act_live = QAction("Predicción en Vivo", self)
        act_live.triggered.connect(lambda: self.load_mode("live"))
        menu.addAction(act_live)

        # Salir
        menu.addSeparator()
        act_exit = QAction("Salir", self)
        act_exit.triggered.connect(self.close)
        menu.addAction(act_exit)

    def clear_docks(self):
        """Elimina todos los docks que tengamos abiertos."""
        for dock in self.current_docks:
            self.removeDockWidget(dock)
            dock.deleteLater()
        self.current_docks = []

    def load_mode(self, mode_key: str):
        """
        Limpia los docks actuales y crea los nuevos
        para el modo indicado por mode_key.
        """
        # 1) Quitar viejos
        self.clear_docks()
        # 2) Llamamos a la fábrica que nos da TODOS los docks de ese modo
        for dock in self.mode_map[mode_key]:
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)
            self.current_docks.append(dock)

    # ——— Fabricantes de docks para cada modo ———

    def _make_capture_dock(self) -> QDockWidget:
        """
        Modo Captura y Segmentación:
          - widget principal de captura (incluye 2D, 3D y heatmap)
        """
        w = CaptureWidget()
        dock = QDockWidget("Captura y Segmentación", self)
        dock.setWidget(w)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        return dock

    def _make_training_dock(self) -> QDockWidget:
        """
        TODO Modo Entrenamiento:
        aquí más adelante pondrás TrainingWidget:

            dock = QDockWidget("Entrenamiento", self)
            dock.setWidget( TrainingWidget() )
            return dock

        ...pero de momento un placeholder.
        """
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        lbl = QLabel("Módulo de entrenamiento\n(implementación pendiente)")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        dock = QDockWidget("Entrenamiento", self)
        dock.setWidget(placeholder)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        return dock

    def _make_offline_dock(self) -> QDockWidget:
        """
        TODO Modo Visualización Offline:
        aquí iría tu OfflineWidget.
        """
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        lbl = QLabel("Visualización Offline\n(implementación pendiente)")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        dock = QDockWidget("Visualización Offline", self)
        dock.setWidget(placeholder)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        return dock

    def _make_live_dock(self) -> QDockWidget:
        """
        TODO Modo Predicción en Vivo:
        aquí irá tu LiveWidget (2D, 3D, heatmap + resultado).
        """
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        lbl = QLabel("Predicción en Vivo\n(implementación pendiente)")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        dock = QDockWidget("Predicción en Vivo", self)
        dock.setWidget(placeholder)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        return dock