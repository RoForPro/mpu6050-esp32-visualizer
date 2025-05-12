# ui/main.py

import os
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QAction, QWidget, QLabel, QVBoxLayout
)
from PyQt5.QtCore import Qt

import config
from ui.widgets.capture_widget import CaptureWidget
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
            "capture": self._create_capture_docks,
            "training": self._create_training_docks,
            "offline": self._create_offline_docks,
            "live": self._create_live_docks,
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
        factories = self.mode_map[mode_key]()
        for dock in factories:
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)
            self.current_docks.append(dock)

    # ——— Fabricantes de docks para cada modo ———

    def _create_capture_docks(self):
        docks = []
        # 1) Un dock 2D por sensor
        from visualization.plot2d import Plot2DWidget
        for sensor_cfg in config.SENSORS:
            w = Plot2DWidget(sensor_id=sensor_cfg['id'], window_size=config.WINDOW_SIZE)
            dock = QDockWidget(f"2D — {sensor_cfg['id']}", self)
            dock.setWidget(w)
            docks.append(dock)

        # 2) Dock 3D global
        # from visualization.renderer3d import Renderer3DWidget
        # w3 = Renderer3DWidget()
        # dock3 = QDockWidget("Vista 3D", self)
        # dock3.setWidget(w3)
        # docks.append(dock3)

        # 3) (Opcional futuro) Dock Heatmap
        # from visualization.heatmap import HeatmapWidget
        # wh = HeatmapWidget()
        # dockh = QDockWidget("Heatmap", self)
        # dockh.setWidget(wh)
        # docks.append(dockh)

        return docks

    def _create_training_docks(self):
        # por ahora placeholder; en breve lo cambias por tu TrainingWidget()
        dock = QDockWidget("Entrenamiento", self)
        placeholder = QLabel("Entrenamiento – pendiente")
        placeholder.setAlignment(Qt.AlignCenter)
        dock.setWidget(placeholder)
        return [dock]

    def _create_offline_docks(self):
        dock = QDockWidget("Visualización Offline", self)
        placeholder = QLabel("Offline – pendiente")
        placeholder.setAlignment(Qt.AlignCenter)
        dock.setWidget(placeholder)
        return [dock]

    def _create_live_docks(self):
        docks = []
        # 1) 2D por sensor (igual que captura)
        from visualization.plot2d import Plot2DWidget
        for sensor_cfg in config.SENSORS:
            w = Plot2DWidget(sensor_id=sensor_cfg['id'], window_size=config.WINDOW_SIZE)
            dock = QDockWidget(f"2D — {sensor_cfg['id']}", self)
            dock.setWidget(w)
            docks.append(dock)

        # 2) 3D global
        from visualization.renderer3d import Renderer3DWidget
        w3 = Renderer3DWidget()
        dock3 = QDockWidget("Vista 3D", self)
        dock3.setWidget(w3)
        docks.append(dock3)

        # 3) Resultado de predicción
        dockr = QDockWidget("Resultado predicción", self)
        placeholder = QLabel("Resultado — pendiente")
        placeholder.setAlignment(Qt.AlignCenter)
        dockr.setWidget(placeholder)
        docks.append(dockr)

        return docks