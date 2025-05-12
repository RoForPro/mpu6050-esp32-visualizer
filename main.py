import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Biomecánico v3.2")
        self.resize(1200, 800)

        # Menú
        menu = self.menuBar().addMenu("Modo")
        actions = {
            "Captura de datos": self.show_capture,
            "Entrenamiento de modelos": self.show_training,
            "Visualización offline": self.show_offline,
            "Predicción": self.show_live
        }
        for name, slot in actions.items():
            # a = self.menuBar().addMenu(name)
            a = menu.addAction(name)
            a.triggered.connect(slot)

        # Docks
        self.capture_dock = QDockWidget("Captura & Etiquetado", self)
        # self.capture_dock.setWidget(CaptureWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.capture_dock)

        self.training_dock = QDockWidget("Entrenamiento", self)
        # self.training_dock.setWidget(TrainingWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.training_dock)
        self.training_dock.hide()

        self.offline_dock = QDockWidget("Visualización Offline", self)
        # self.offline_dock.setWidget(OfflineVisualizationWidget())
        self.addDockWidget(Qt.BottomDockWidgetArea, self.offline_dock)
        self.offline_dock.hide()

        self.live_dock = QDockWidget("Predicción en Vivo", self)
        # self.live_dock.setWidget(LivePredictionWidget())
        self.addDockWidget(Qt.BottomDockWidgetArea, self.live_dock)
        self.live_dock.hide()

    def show_capture(self):
        for d in (self.training_dock, self.offline_dock, self.live_dock):
            d.hide()
        self.capture_dock.show()

    def show_training(self):
        for d in (self.capture_dock, self.offline_dock, self.live_dock):
            d.hide()
        self.training_dock.show()

    def show_offline(self):
        for d in (self.capture_dock, self.training_dock, self.live_dock):
            d.hide()
        self.offline_dock.show()

    def show_live(self):
        for d in (self.capture_dock, self.training_dock, self.offline_dock):
            d.hide()
        self.live_dock.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.showMaximized()
    sys.exit(app.exec_())
