# visualization/renderer3d.py

from PyQt5 import QtWidgets
from skeleton_renderer import Skeleton3D

class Renderer3DWidget(QtWidgets.QWidget):
    """
    Widget contenedor para la vista 3D de esqueleto.
    Encapsula tu clase Skeleton3D para poder incrustarla en layouts Qt.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Instanciamos tu objeto de render 3D (usa PyOpenGL / GLViewWidget internamente)
        self.viewer = Skeleton3D()

        # Lo metemos en un layout para que Qt gestione el tamaño
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.viewer)
        self.setLayout(layout)

    def update_data(self, reading: dict):
        """
        Proxy a tu método de actualización:
        :param reading: {'sensor_id', 'timestamp', 'yaw', 'pitch', 'roll', …}
        """
        yaw   = reading.get('yaw',   0.0)
        pitch = reading.get('pitch', 0.0)
        roll  = reading.get('roll',  0.0)
        # Llama al update de tu Skeleton3D
        self.viewer.update(yaw, pitch, roll)
