# visualization/plot2d.py

import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg

class Plot2DWidget(pg.PlotWidget):
    """
    Widget para mostrar en tiempo real yaw, pitch y roll
    de un IMU. Mantiene una ventana deslizante de tamaño fijo.
    Si se le pasa sensor_id, solo dibuja datos de ese sensor.
    """

    def __init__(self, sensor_id: str = None, window_size: int = 200, parent=None):
        """
        :param sensor_id: si no es None, filtra solo readings con matching sensor_id
        :param window_size: número de muestras a mostrar en el eje X
        """
        super().__init__(parent=parent)
        self.sensor_id = sensor_id
        self.window_size = window_size

        # Datos iniciales (arrays circulares)
        self._data = {
            'yaw':   np.zeros(window_size, dtype=float),
            'pitch': np.zeros(window_size, dtype=float),
            'roll':  np.zeros(window_size, dtype=float)
        }
        self._ptr = 0  # índice de inserción en ventana deslizante

        # Setup del plot
        self.setTitle(f"{'Sensor ' + sensor_id if sensor_id else 'IMU'} – Yaw/Pitch/Roll")
        self.addLegend()
        self.setLabel('left', 'Ángulo (°)')
        self.setLabel('bottom', 'Muestra')

        # Curvas con colores estándar
        self.curves = {
            'yaw':   self.plot(pen='r', name='Yaw'),
            'pitch': self.plot(pen='g', name='Pitch'),
            'roll':  self.plot(pen='b', name='Roll')
        }

        # Rango fijo de muestras (0 … window_size−1)
        self._x = np.arange(window_size)

    def update_data(self, reading: dict):
        """
        Añade una nueva lectura al buffer y actualiza las curvas.
        :param reading: {'sensor_id','timestamp','yaw','pitch','roll'}
        """
        # Filtrado opcional por sensor
        if self.sensor_id and reading.get('sensor_id') != self.sensor_id:
            return

        # Añadimos cada valor al buffer circular
        for key in ('yaw', 'pitch', 'roll'):
            buf = self._data[key]
            buf[self._ptr] = reading.get(key, 0.0)

        # Avanzamos puntero (circular)
        self._ptr = (self._ptr + 1) % self.window_size

        # Para simplificar, reordenamos los datos para setData
        # desde ptr+1 … end, 0…ptr para ver la ventana deslizante
        idx = np.roll(self._x, -self._ptr)
        for key, curve in self.curves.items():
            curve.setData(idx, np.roll(self._data[key], -self._ptr))
