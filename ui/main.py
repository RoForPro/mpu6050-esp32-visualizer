# ui/main.py

import os
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QAction, QWidget, QLabel, QVBoxLayout
)
from PyQt5.QtCore import Qt

import config
from ui.widgets.capture_widget import CaptureWidget
from ui.widgets.offline_widget import OfflineWidget
from ui.widgets.training_widget import TrainingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Biomecánico v4.0")
        self.resize(1200, 800)

        # 1) Creación única de cada dock (y su widget)
        # — Capture —
        self.capture_dock = QDockWidget("Captura y Segmentación", self)
        self.capture_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.capture_dock.setWidget(CaptureWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.capture_dock)

        # — Offline —
        self.offline_dock = QDockWidget("Visualización Offline", self)
        self.offline_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.offline_dock.setWidget(OfflineWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.offline_dock)

        # — Training —
        self.training_dock = QDockWidget("Entrenamiento", self)
        self.training_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.training_dock.setWidget(TrainingWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.training_dock)

        # — Live (placeholder) —
        self.live_dock = QDockWidget("Predicción en Vivo", self)
        self.live_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        ph_live = QWidget()
        lay_l = QVBoxLayout(ph_live)
        lbl_l = QLabel("Predicción en Vivo\n(implementación pendiente)")
        lbl_l.setAlignment(Qt.AlignCenter)
        lay_l.addWidget(lbl_l)
        self.live_dock.setWidget(ph_live)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.live_dock)

        # 2) Las mantenemos en una lista para iterar fácilmente
        self.all_docks = [
            self.capture_dock,
            self.offline_dock,
            self.training_dock,
            self.live_dock
        ]

        # 3) Construimos el menú
        self._setup_menu()

        # 4) Ocultamos todo salvo el modo por defecto
        self._show_only(self.capture_dock)

    def _setup_menu(self):
        modo_menu = self.menuBar().addMenu("Modo")

        # Helper para cada acción
        def make_action(text, dock):
            act = QAction(text, self)
            act.triggered.connect(lambda: self._show_only(dock))
            return act

        modo_menu.addAction(make_action("Captura y Segmentación", self.capture_dock))
        modo_menu.addAction(make_action("Visualización Offline", self.offline_dock))
        modo_menu.addAction(make_action("Entrenamiento", self.training_dock))
        modo_menu.addAction(make_action("Predicción en Vivo", self.live_dock))
        modo_menu.addSeparator()
        modo_menu.addAction(QAction("Salir", self, triggered=self.close))

    def _show_only(self, dock_to_show: QDockWidget):
        """
        Muestra únicamente el dock indicado y oculta los demás.
        """
        for dock in self.all_docks:
            dock.setVisible(dock is dock_to_show)
