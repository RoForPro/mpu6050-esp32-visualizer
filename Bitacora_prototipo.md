
# 🗂️ Bitácora del proyecto – Prototipo con ESP32 + MPU6050

## 🔰 Fase 0: Preparación y prototipado inmediato

---

### 📦 1. **Hardware utilizado**

- ✅ ESP32-WROVER-E (placa de desarrollo)
- ✅ Módulo MPU6050 (GY-521)
- ✅ Cables dupont / sujeción básica (muñeca o cadera)
- ✅ USB para conexión a PC

---

### 🔌 2. **Conexiones físicas MPU6050 ↔ ESP32**

| MPU6050 Pin | ESP32 Pin |
|-------------|-----------|
| VCC         | 3.3V      |
| GND         | GND       |
| SDA         | GPIO21    |
| SCL         | GPIO22    |
| INT         | GPIO25    |

---

### 💻 3. **Software y entorno de desarrollo**

- ✅ **Arduino IDE**: para cargar código al ESP32
- ✅ **PyCharm Professional** (con licencia educativa)
- ✅ Python instalado (desde python.org)
- ✅ Entorno virtual creado con `virtualenv` en PyCharm
- ✅ Bibliotecas instaladas en el entorno:
  ```bash
  pip install pyserial matplotlib pandas numpy scikit-learn
  ```

---

### 🛠️ 4. **Sketch de Arduino cargado en ESP32**

- 🧠 Usa la librería **MPU6050_6Axis_MotionApps20**
- ✅ DMP activado
- ✅ Imprime orientación: `timestamp_ms, yaw, pitch, roll` por puerto serie
- ✅ Frecuencia estable: 115200 baudios
- ✅ Frecuencia I2C ajustada a 100kHz para evitar errores

---

### 🧪 5. **Primer script de captura de datos (Python)**

- 📁 Guardado en: `scripts/captura_continua.py`
- 🔌 Escucha en COM4 (configurable)
- 💾 Guarda CSV en `data/datos_continuos_YYYYMMDD_HHMMSS.csv`
- 📊 Estructura del CSV:
  ```
  timestamp_ms,yaw,pitch,roll
  12133,45.1,-2.3,6.9
  ...
  ```

---

### 🧭 6. Estado del flujo completo (prototipo)

| Etapa                     | Estado     | Comentario                              |
|---------------------------|------------|------------------------------------------|
| Sensor conectado           | ✅         | MPU6050 con ESP32                        |
| Lectura de orientación     | ✅         | Yaw, Pitch, Roll vía DMP                 |
| Captura continua en Python | ✅         | CSV automático funcionando               |
| Visualización en vivo      | 🔜         | Próximo paso con matplotlib              |
| Etiquetado manual          | 🔜         | Próximo paso (manual o con marcador)     |
| Clasificación IA           | 🔜         | En fases posteriores                     |

---

### 📂 Estructura del proyecto

```
tu_proyecto/
│
├── data/                  ← CSV de capturas
├── notebooks/             ← Exploración y visualización
├── scripts/               ← Python de captura, visualización, etc.
├── main.py                ← (opcional, punto de entrada)
├── requirements.txt       ← Bibliotecas usadas
└── README.md              ← Documentación general
```

---

## 📌 Siguiente paso sugerido

- ✅ Probar `captura_continua.py`
- 🔜 Avanzar a `captura_marcada.py` (versión B)
- 🔜 Visualización en vivo (`visualizar_en_tiempo_real.py`)
- 🔜 Exploración y etiquetado en Jupyter

## Bitácora del Proyecto - Visualización en Tiempo Real (MPU6050 - Roll, Pitch, Yaw)

### 🌟 Estado actual
- Lectura de datos desde el MPU6050 conectada a ESP32 funcionando correctamente.
- Visualización en tiempo real de los valores de **Yaw**, **Pitch** y **Roll** implementada exitosamente con **PyQtGraph**.
- Se ha resuelto el problema de que la curva no se deslizara adecuadamente.

---

### ✅ Pasos logrados hasta ahora:

#### 1. Lectura y captura de datos (modo consola y CSV)
- Se probó la lectura de datos usando `pyserial`.
- Se confirmó que el sketch del ESP32 imprime datos en el formato esperado:
  ```
  timestamp,yaw,pitch,roll
  88179,34.10,0.51,-0.19
  ```
- Se creó un script `captura_datos.py` para almacenar los datos recibidos en un archivo CSV.
- Confirmado que los valores cambian correctamente en consola conforme se mueve el sensor.

#### 2. Intentos con Matplotlib
- Se intentó usar `matplotlib.animation.FuncAnimation`.
- La ventana se abría pero no se actualizaba correctamente o se quedaba congelada.
- Problemas de rendimiento y de refresco de la gráfica en tiempo real.

#### 3. Cambio a PyQtGraph (solución óptima)
- Se instaló `pyqtgraph` y `PyQt5` con:
  ```bash
  pip install pyqtgraph PyQt5
  ```
- Se creó una ventana gráfica usando `GraphicsLayoutWidget`.
- Se configuró un `QTimer` para refrescar la gráfica cada 50ms.
- Se lanzó un hilo con `threading.Thread` para leer datos del puerto serie en paralelo.
- Se extrajeron los valores de **timestamp**, **yaw**, **pitch** y **roll** separados por comas.
- Se implementó una **ventana deslizante** para mostrar siempre las últimas 200 muestras de cada variable.
- Las gráficas se actualizan correctamente y se desplazan con el tiempo.

---

### ⚙️ Siguientes pasos sugeridos
- Visualizar las tres variables (Yaw, Pitch y Roll) en subgráficas simultáneas.
- Permitir guardar los datos en CSV desde PyQtGraph.
- Implementar una versión con **marcadores manuales** (inicio/fin de repeticiones).
- Preparar la captura para etiquetado posterior y entrenamiento de modelos IA.

---

📅 Fecha de actualización: 2025-04-14

