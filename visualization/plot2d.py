# visualization/plot2d.py

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui

# 1) Configuración global de tema oscuro
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')
pg.setConfigOption('antialias', True)

class Plot2DWidget(pg.PlotWidget):
    """
    Widget en tiempo real para mostrar yaw, pitch y roll.
    Buffer circular con ventana fija y scroll continuo.
    """

    def __init__(self, sensor_id: str = None, window_size: int = 200, parent=None):
        """
        :param sensor_id: si no es None, filtra por este sensor_id
        :param window_size: cuántas muestras se muestran en pantalla
        """
        super().__init__(parent=parent)
        self.sensor_id = sensor_id
        self.window_size = window_size

        # Buffer circular para cada señal
        self._data = {
            'yaw':   np.zeros(window_size, dtype=float),
            'pitch': np.zeros(window_size, dtype=float),
            'roll':  np.zeros(window_size, dtype=float)
        }
        self._ptr = 0  # posición de inserción

        # Configuración del plot
        self.setTitle(
            f"{'Sensor ' + sensor_id if sensor_id else 'IMU'} – Yaw/Pitch/Roll",
            color='w'
        )
        # self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel('left', 'Ángulo (°)', **{'color':'w'})
        self.setLabel('bottom', 'Muestra', **{'color':'w'})

        # Curvas: si solo quieres una, borra las dos no deseadas
        self.curves = {
            'yaw':   self.plot(pen=pg.mkPen('r', width=1.5), name='Yaw'),
            'pitch': self.plot(pen=pg.mkPen('g', width=1.5), name='Pitch'),
            'roll':  self.plot(pen=pg.mkPen('b', width=1.5), name='Roll')
        }

        # Eje X fijo de 0 a window_size−1
        self._x = np.arange(window_size)

    def update_data(self, reading: dict):
        """
        Añade reading al buffer y actualiza la curva.
        :param reading: {'sensor_id','timestamp','yaw','pitch','roll'}
        """
        # Filtrado por sensor
        if self.sensor_id and reading.get('sensor_id') != self.sensor_id:
            return

        # Insertamos valores en buffer circular
        for key in ('yaw', 'pitch', 'roll'):
            self._data[key][self._ptr] = reading.get(key, 0.0)

        # Avanzamos puntero (circular)
        self._ptr = (self._ptr + 1) % self.window_size

        # Para cada curva, extraemos la ventana deslizante en orden
        rolled_x = self._x  # eje X siempre 0…N−1
        for key, curve in self.curves.items():
            yview = np.roll(self._data[key], -self._ptr)
            curve.setData(rolled_x, yview)
