# scripts/skeleton_renderer.py

import numpy as np
import pyqtgraph.opengl as gl


def _rotation_matrix(yaw, pitch, roll):
    """Matriz de rotación Z→Y→X."""
    cy, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    Rz = np.array([[cy, -sy, 0],
                   [sy, cy, 0],
                   [0, 0, 1]])
    Ry = np.array([[cp, 0, sp],
                   [0, 1, 0],
                   [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0],
                   [0, cr, -sr],
                   [0, sr, cr]])
    return Rz @ Ry @ Rx


class Skeleton3D:
    """Esqueleto 3D de dos huesos: upper arm y forearm."""

    def __init__(self,
                 upper_len: float = 4.0,
                 fore_len: float = 3.5,
                 distance: float = 40,
                 azimuth: float = 45,
                 elevation: float = 30):
        # Ventana GL
        self.view = gl.GLViewWidget()
        self.view.setWindowTitle('Esqueleto 3D IMU')
        self.view.setCameraPosition(distance=distance,
                                    azimuth=azimuth,
                                    elevation=elevation)
        # Grid
        grid = gl.GLGridItem()
        grid.setSize(20, 20);
        grid.setSpacing(1, 1)
        self.view.addItem(grid)

        # Parámetros de huesos
        self.upper_len = upper_len
        self.fore_len = fore_len

        # Coords iniciales de los huesos
        # Upper arm: del origen al (0,0,upper_len)
        p0 = np.array([0, 0, 0])
        p1 = np.array([0, 0, self.upper_len])
        # Forearm: del joint al joint+fore_len
        p2 = p1 + np.array([0, 0, self.fore_len])

        # Linea upper arm
        self.bone1 = gl.GLLinePlotItem(pos=np.vstack([p0, p1]),
                                       width=4, antialias=True,
                                       color=(0, 0.8, 0, 1))
        self.view.addItem(self.bone1)
        # Linea forearm
        self.bone2 = gl.GLLinePlotItem(pos=np.vstack([p1, p2]),
                                       width=4, antialias=True,
                                       color=(0, 0.6, 1, 1))
        self.view.addItem(self.bone2)

        self.view.show()

    def update(self, yaw: float, pitch: float, roll: float):
        """Rota ambos huesos según yaw/pitch/roll del IMU."""
        R = _rotation_matrix(yaw, pitch, roll)

        # Upper arm
        p0 = np.array([0, 0, 0])
        p1 = R.dot(np.array([0, 0, self.upper_len]))
        # Forearm: pivot en p1
        p2 = p1 + R.dot(np.array([0, 0, self.fore_len]))

        pts1 = np.vstack([p0, p1])
        pts2 = np.vstack([p1, p2])

        self.bone1.setData(pos=pts1)
        self.bone2.setData(pos=pts2)
