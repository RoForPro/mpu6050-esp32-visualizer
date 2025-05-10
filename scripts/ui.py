# scripts/ui.py

import pandas as pd
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from .skeleton_renderer import Skeleton3D
from .acquisition import SerialReader
from .predictor import Predictor
from .training import train_model  # si quieres dejar el pipeline aquí

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, model_path, port, baud):
        super().__init__()
        self.setWindowTitle("MPU6050 – Demo Completo")
        self.resize(1200, 800)

        # — SerialReader y Predictor (antes de los docks) —
        self.acq       = SerialReader(port, baud, raw_csv="data/datos_ejercicio_raw.csv")
        self.acq.on_line        = self._on_line
        self.acq.on_segment_end = self._on_segment_end
        self.predictor = Predictor(model_path)

        # — Configuración de todos los docks —
        self._setup_2d_plot()
        self._setup_3d_skeleton()
        self._setup_prediction_dock()
        self._setup_heatmap_dock()
        self._setup_offline_dock()
        self._setup_menu()

        # — Iniciar adquisición —
        self.acq.start()

    # ─── DOCKS ──────────────────────────────────────────────────────────

    def _setup_2d_plot(self):
        self.plot2d = pg.PlotWidget(title="Yaw / Pitch / Roll")
        self.plot2d.addLegend()
        self.curves = {
            'yaw':   self.plot2d.plot(pen='r', name='Yaw'),
            'pitch': self.plot2d.plot(pen='g', name='Pitch'),
            'roll':  self.plot2d.plot(pen='b', name='Roll'),
        }
        dock = QtWidgets.QDockWidget("Gráfica 2D", self)
        dock.setWidget(self.plot2d)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    def _setup_3d_skeleton(self):
        self.sk = Skeleton3D()
        dock = QtWidgets.QDockWidget("Esqueleto 3D", self)
        dock.setWidget(self.sk.view)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def _setup_prediction_dock(self):
        self.lbl = QtWidgets.QLabel("Esperando...", self)
        self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl.setStyleSheet("background: rgba(0,0,0,150); color: white;")
        dock = QtWidgets.QDockWidget("Predicción", self)
        dock.setWidget(self.lbl)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    def _setup_heatmap_dock(self):
        placeholder = QtWidgets.QLabel("Heatmap\n(próximamente)", self)
        placeholder.setAlignment(QtCore.Qt.AlignCenter)
        placeholder.setStyleSheet("border: 1px dashed gray;")
        dock = QtWidgets.QDockWidget("Mapa de Calor", self)
        dock.setWidget(placeholder)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock.setFeatures(dock.DockWidgetMovable | dock.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    def _setup_offline_dock(self):
        """Dock para navegar repeticiones offline."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        # Plot
        self.offlinePlot = pg.PlotWidget(title="Offline: Yaw/Pitch/Roll")
        self.offlinePlot.addLegend()
        layout.addWidget(self.offlinePlot)
        # Botones
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_prev = QtWidgets.QPushButton("⟨ Anterior")
        self.btn_next = QtWidgets.QPushButton("Siguiente ⟩")
        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_next)
        layout.addLayout(btn_layout)
        # Conexiones
        self.btn_prev.clicked.connect(self._offline_prev)
        self.btn_next.clicked.connect(self._offline_next)
        # Dock
        self.dockOffline = QtWidgets.QDockWidget("Visualización Offline", self)
        self.dockOffline.setWidget(container)
        self.dockOffline.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.dockOffline.setFeatures(self.dockOffline.DockWidgetMovable |
                                     self.dockOffline.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dockOffline)
        self.dockOffline.hide()  # arranca oculto

    # ─── MENÚ ────────────────────────────────────────────────────────────

    def _setup_menu(self):
        menubar = self.menuBar()

        # 1) Captura (adquisición + segmentación)
        m_cap = menubar.addMenu("Captura")
        m_cap.addAction("Iniciar adquisición",  self.acq.start)
        m_cap.addAction("Detener adquisición",  self.acq.stop)
        m_cap.addSeparator()
        m_cap.addAction("Iniciar Correcto",     lambda: self.acq.tag_start("Correcto"))
        m_cap.addAction("Finalizar Correcto",   self.acq.tag_end)
        m_cap.addSeparator()
        m_cap.addAction("Iniciar Incorrecto",   lambda: self.acq.tag_start("Incorrecto"))
        m_cap.addAction("Finalizar Incorrecto", self.acq.tag_end)

        # 2) Pipeline
        m_pipe = menubar.addMenu("Pipeline")
        m_pipe.addAction("Entrenar modelo",      self._on_train)
        m_pipe.addAction("Mostrar Offline",      self._on_show_offline)
        m_pipe.addAction("Predicción en vivo",   lambda: None)

        menubar.addAction("Salir", self.close)

    # ─── CALLBACKS 2D / 3D / PREDICCIÓN ────────────────────────────────

    def _on_line(self, ts, y, p, r):
        # buffers
        if not hasattr(self, 'yaw_buf'):
            self.WINDOW_SIZE = 200
            self.yaw_buf   = []; self.pitch_buf = []; self.roll_buf = []
        self.yaw_buf.append(y);   self.pitch_buf.append(p); self.roll_buf.append(r)
        if len(self.yaw_buf) > self.WINDOW_SIZE:
            self.yaw_buf.pop(0); self.pitch_buf.pop(0); self.roll_buf.pop(0)
        # actualizar 2D
        x = list(range(len(self.yaw_buf)))
        self.curves['yaw'].setData(x, self.yaw_buf)
        self.curves['pitch'].setData(x, self.pitch_buf)
        self.curves['roll'].setData(x, self.roll_buf)
        # actualizar 3D
        self.sk.update(y, p, r)

    def _on_segment_end(self, tag, samples):
        pred, prob = self.predictor.predict_segment(samples)
        text = ("✔️ CORRECTO" if pred else "❌ INCORRECTO")
        bg    = ("rgba(0,150,0,200)" if pred else "rgba(150,0,0,200)")
        self.lbl.setStyleSheet(f"background: {bg}; color: white;")
        self.lbl.setText(f"{text}\nProb: {prob:.2f}")

    # ─── ENTRENAMIENTO ─────────────────────────────────────────────────

    def _on_train(self):
        train_model("data/datos_ejercicio.csv",
                    "models/modelo_prototipo.joblib")
        QtWidgets.QMessageBox.information(
            self, "Pipeline", "Entrenamiento completado.\nModelo guardado."
        )

    # ─── VISUALIZACIÓN OFFLINE ─────────────────────────────────────────

    def _on_show_offline(self):
        # Carga datos y arranca en primer índice
        df = pd.read_csv("data/datos_ejercicio.csv")
        self.offline_groups = [(rid, g) for rid, g in df.groupby("rep_id")]
        self.offline_index = 0
        self._update_offline_plot()
        self.dockOffline.show()

    def _update_offline_plot(self):
        rid, group = self.offline_groups[self.offline_index]
        # normalizamos tiempo y convertimos a arrays
        tiempo = ((group["timestamp"] - group["timestamp"].iloc[0]) / 1000.0).to_numpy()
        yaw = group["yaw"].to_numpy()
        pitch = group["pitch"].to_numpy()
        roll = group["roll"].to_numpy()

        self.offlinePlot.clear()
        self.offlinePlot.plot(tiempo, yaw, pen='r', name='Yaw')
        self.offlinePlot.plot(tiempo, pitch, pen='g', name='Pitch')
        self.offlinePlot.plot(tiempo, roll, pen='b', name='Roll')
        etiqueta = group["etiqueta"].iloc[0]
        self.offlinePlot.setTitle(f"Repetición {rid} – {etiqueta}")

    def _offline_prev(self):
        if self.offline_index > 0:
            self.offline_index -= 1
            self._update_offline_plot()

    def _offline_next(self):
        if self.offline_index < len(self.offline_groups) - 1:
            self.offline_index += 1
            self._update_offline_plot()

    # ─── CIERRE LIMPIO ─────────────────────────────────────────────────

    def closeEvent(self, event):
        self.acq.stop()
        QtCore.QThread.msleep(100)
        event.accept()
