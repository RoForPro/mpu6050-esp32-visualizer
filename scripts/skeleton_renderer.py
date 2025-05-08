# skeleton_renderer.py

import numpy as np
import pyqtgraph.opengl as gl

def _rotation_matrix(yaw, pitch, roll):
    """Matriz Z→Y→X como antes."""
    cy, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    cr, sr = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    Rz = np.array([[ cy, -sy, 0],
                   [ sy,  cy, 0],
                   [  0,   0, 1]])
    Ry = np.array([[ cp, 0, sp],
                   [  0, 1,  0],
                   [-sp, 0, cp]])
    Rx = np.array([[1,   0,    0],
                   [0,  cr, -sr],
                   [0,  sr,  cr]])
    return Rz @ Ry @ Rx

class Skeleton3D:
    """
    Representa un “esqueleto” de un solo hueso (por ahora) que rota con yaw/pitch/roll.
    En el futuro puedes reemplazar bone/joints por un modelo completo.
    """
    def __init__(self, distance=40, azimuth=45, elevation=30):
        self.view = gl.GLViewWidget()
        self.view.setWindowTitle('Esqueleto 3D IMU')
        self.view.setCameraPosition(distance=distance,
                                    azimuth=azimuth,
                                    elevation=elevation)
        # grid
        grid = gl.GLGridItem()
        grid.setSize(20,20); grid.setSpacing(1,1)
        self.view.addItem(grid)
        # hueso: línea de longitud 5 en Z
        pts = np.array([[0,0,0],[0,0,5]], dtype=float)
        self.bone = gl.GLLinePlotItem(pos=pts, width=4, antialias=True,
                                      color=(0,0.8,0,1))
        self.view.addItem(self.bone)
        # articulaciones: dos esferas
        self.joints = gl.GLScatterPlotItem(pos=pts, size=8,
                                           color=(1,0,0,1), pxMode=False)
        self.view.addItem(self.joints)
        self.view.show()

    def update(self, yaw, pitch, roll):
        """Aplica la misma rotación al hueso y las articulaciones."""
        R = _rotation_matrix(yaw, pitch, roll)
        base = np.array([0,0,0])
        tip  = R.dot(np.array([0,0,5]))
        pts = np.vstack([base, tip])
        self.bone.setData(pos=pts)
        self.joints.setData(pos=pts)
