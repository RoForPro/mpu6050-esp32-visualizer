# core/imu/imu.py

import time
import threading
import queue
import serial

class IMUSensor:
    """
    Interfaz a un único sensor inertial (IMU) vía puerto serie,
    con lectura en segundo plano y almacenamiento en cola.
    """

    def __init__(self, sensor_id: str, port: str, baud_rate: int):
        """
        :param sensor_id: identificador único del sensor (e.g. "imu1")
        :param port: puerto serie (e.g. "COM9" o "/dev/ttyUSB0")
        :param baud_rate: velocidad de comunicación (e.g. 115200)
        """
        self.id = sensor_id
        # timeout=0 para lectura no bloqueante
        self.ser = serial.Serial(port, baud_rate, timeout=0)
        print("Puerto serie abierto:", self.ser.name)
        time.sleep(2)  # Dar tiempo a estabilizar el ESP32
        # Vacía buffers iniciales
        self.ser.reset_input_buffer()

        # Buffer de texto parcial y cola de líneas completas
        self._text_buffer = ""
        self._queue = queue.Queue()

        # Señal de parada y hilo lector
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def _reader_loop(self):
        """
        Hilo en segundo plano que descarga todo el buffer de serie
        y encola líneas completas.
        """
        while not self._stop_event.is_set():
            n = self.ser.in_waiting
            if n:
                raw_bytes = self.ser.read(n)
                chunk = raw_bytes.decode('utf-8', errors='ignore')
                self._text_buffer += chunk
                # Separa líneas completas
                while "\n" in self._text_buffer:
                    line, self._text_buffer = self._text_buffer.split("\n", 1)
                    self._queue.put(line.strip())
            else:
                # Evitamos busy‐wait continuo
                time.sleep(0.001)

    def read_now(self) -> list:
        """
        Extrae todas las líneas pendientes de la cola,
        las parsea y devuelve una lista de dicts con datos válidos.
        """
        readings = []
        while True:
            parsed = None
            try:
                raw = self._queue.get_nowait()
                parsed = self._parse_line(raw)
            except queue.Empty:
                break
            if parsed:
                readings.append(parsed)
        return readings

    def _parse_line(self, line: str) -> dict:
        """
        Lee una línea del sensor y devuelve un diccionario con:
        { 'sensor_id': str, 'timestamp': float, 'yaw': float, 'pitch': float, 'roll': float }
        
        Args:
            line: línea de texto a parsear con el formato "timestamp,yaw,pitch,roll"
        """
        try:
            # line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            # if not line:
            #     return None

            parts = line.split(',')
            if len(parts) != 4:  # Modificar en caso de cambio de formato de envío de datos el ESP32
                return None
            
            timestamp, yaw, pitch, roll = map(float, parts)
            
            return {
                'sensor_id': self.id,
                'timestamp': timestamp,
                'yaw': yaw,
                'pitch': pitch,
                'roll': roll
            }
        
        except (ValueError, serial.SerialException):
            return None

    def close(self):
        """
        Detiene el hilo lector y cierra el puerto serie.
        """
        self._stop_event.set()
        self._thread.join()
        if self.ser.is_open:
            self.ser.close()