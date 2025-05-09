# scripts/ui.py

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from .skeleton_renderer import Skeleton3D
from .acquisition import SerialReader
from .predictor import Predictor

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, model_path, port, baud):
        super().__init__()
        self.setWindowTitle("MPU6050 Demo con DockWidgets")
        self.resize(1200, 800)
        
        # Primero inicializamos SerialReader y Predictor
        self.acq = SerialReader(port, baud, raw_csv="data/datos_ejercicio_raw.csv")
        self.acq.on_line = self._on_line
        self.acq.on_segment_end = self._on_segment_end
        self.predictor = Predictor(model_path)

        # Luego configuramos la interfaz gráfica
        self._setup_2d_plot()
        self._setup_3d_skeleton()
        self._setup_prediction_dock()
        self._setup_heatmap_dock()
        self._setup_menu()
        
        # Finalmente iniciamos la adquisición
        self.acq.start()

    def _setup_menu(self):
        menubar = self.menuBar()
        m_seg = menubar.addMenu("Segmentación")
        m_seg.addAction("Iniciar Correcto",  lambda: self.acq.tag_start("Correcto"))
        m_seg.addAction("Finalizar Correcto", self.acq.tag_end)
        m_seg.addSeparator()
        m_seg.addAction("Iniciar Incorrecto", lambda: self.acq.tag_start("Incorrecto"))
        m_seg.addAction("Finalizar Incorrecto", self.acq.tag_end)
        menubar.addAction("Salir", self.close)

    def _setup_2d_plot(self):
        self.plot2d = pg.PlotWidget(title="Yaw / Pitch / Roll")
        self.plot2d.addLegend()
        # Líneas vacías; se rellenan en _on_line
        self.curves = {
            'yaw':   self.plot2d.plot(pen='r', name='Yaw'),
            'pitch': self.plot2d.plot(pen='g', name='Pitch'),
            'roll':  self.plot2d.plot(pen='b', name='Roll'),
        }
        dock2d = QtWidgets.QDockWidget("Gráfica 2D", self)
        dock2d.setWidget(self.plot2d)
        dock2d.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock2d.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2d)

    def _setup_3d_skeleton(self):
        self.sk = Skeleton3D()
        dock3d = QtWidgets.QDockWidget("Esqueleto 3D", self)
        dock3d.setWidget(self.sk.view)
        dock3d.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock3d.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock3d)

    def _setup_prediction_dock(self):
        self.lbl = QtWidgets.QLabel("Esperando...", self)
        self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl.setStyleSheet("background: rgba(0,0,0,150); color: white;")
        dockPred = QtWidgets.QDockWidget("Predicción", self)
        dockPred.setWidget(self.lbl)
        dockPred.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dockPred.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockPred)

    def _setup_heatmap_dock(self):
        placeholder = QtWidgets.QLabel("Heatmap\n(próximamente)", self)
        placeholder.setAlignment(QtCore.Qt.AlignCenter)
        placeholder.setStyleSheet("border: 1px dashed gray;")
        dockHeat = QtWidgets.QDockWidget("Mapa de Calor", self)
        dockHeat.setWidget(placeholder)
        dockHeat.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dockHeat.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockHeat)

    def _on_line(self, ts, y, p, r):
        # Actualizar buffers internos (igual que antes)
        if not hasattr(self, 'yaw_buf'):
            self.WINDOW_SIZE = 200
            self.yaw_buf = []
            self.pitch_buf = []
            self.roll_buf = []

        self.yaw_buf.append(y);   self.pitch_buf.append(p); self.roll_buf.append(r)
        if len(self.yaw_buf) > self.WINDOW_SIZE:
            self.yaw_buf.pop(0); self.pitch_buf.pop(0); self.roll_buf.pop(0)

        x = list(range(len(self.yaw_buf)))
        self.curves['yaw'].setData(x, self.yaw_buf)
        self.curves['pitch'].setData(x, self.pitch_buf)
        self.curves['roll'].setData(x, self.roll_buf)

        # 3D
        self.sk.update(y, p, r)

    def _on_segment_end(self, tag, samples):
        pred, prob = self.predictor.predict_segment(samples)
        if pred == 1:
            text, bg = "✔️ CORRECTO", "rgba(0,150,0,200)"
        else:
            text, bg = "❌ INCORRECTO", "rgba(150,0,0,200)"
        self.lbl.setStyleSheet(f"background: {bg}; color: white;")
        self.lbl.setText(f"{text}\nProb: {prob:.2f}")

    def closeEvent(self, event):
        self.acq.stop()
        QtCore.QThread.msleep(100)
        event.accept()